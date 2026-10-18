"""A chat model that answers from a script, for the conversation loop's tests: no OpenAI."""

import asyncio
import json

from langchain_core.messages import AIMessageChunk


def text(words: str, sleep: float = 0) -> dict:
    """A reply streaming `words` one at a time; it waits `sleep` seconds after the first."""
    return {"text": words, "sleep": sleep}


def calls(*named: tuple[str, dict | str]) -> dict:
    """A reply calling tools at once: (name, arguments), the arguments as the model's JSON (a
    string that isn't JSON makes an invalid call)."""
    return {"calls": named}


class FakeModel:
    """Each call answers with the script's next reply (or raises it, when it's an exception),
    and reports 10 input and 5 output tokens."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.prompts = []
        self.bound = []
        # Each call's config: its LangSmith run id when tracing is on.
        self.configs = []

    def bind_tools(self, tools, **options):
        self.bound.append((tools, options))

        return self

    async def astream(self, messages, config=None):
        self.prompts.append(list(messages))
        self.configs.append(config)
        reply = self.replies.pop(0)

        if isinstance(reply, Exception):
            raise reply

        for index, word in enumerate(reply.get("text", "").split(" ") if "text" in reply else []):
            yield AIMessageChunk(content=word if index == 0 else f" {word}")

            if index == 0 and reply["sleep"]:
                await asyncio.sleep(reply["sleep"])

        chunks = [
            {
                "name": name,
                "args": arguments if isinstance(arguments, str) else json.dumps(arguments),
                "id": f"call-{len(self.prompts)}-{index}",
                "index": index,
            }
            for index, (name, arguments) in enumerate(reply.get("calls", ()))
        ]
        usage = {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}

        yield AIMessageChunk(content="", tool_call_chunks=chunks, usage_metadata=usage)


class FakeTitleModel:
    """The titles' model, answering `title` (no OpenAI)."""

    def __init__(self, title: str = "A chat"):
        self.title = title

    async def ainvoke(self, messages):
        from langchain_core.messages import AIMessage

        usage = {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5}

        return AIMessage(content=self.title, usage_metadata=usage)
