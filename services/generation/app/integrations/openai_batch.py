import io
import json
from functools import cache

from langchain_core.messages import BaseMessage
from openai import AsyncOpenAI
from openai.lib._parsing._completions import type_to_response_format_param
from pydantic import BaseModel

from app.constants.generation import BATCH_MAX_RETRIES, LLM_TIMEOUT_SECONDS, MAX_OUTPUT_TOKENS

COMPLETIONS = "/v1/chat/completions"


@cache
def get_client() -> AsyncOpenAI:
    return AsyncOpenAI(timeout=LLM_TIMEOUT_SECONDS, max_retries=BATCH_MAX_RETRIES)


def request_body(
    model: str, effort: str, messages: list[BaseMessage], schema: type[BaseModel]
) -> dict:
    """A chat completion's body for a batch: the call with_structured_output would make, its
    schema strict (the OpenAI SDK builds it as it does for a direct call)."""
    roles = {"system": "system", "human": "user"}

    return {
        "model": model,
        "reasoning_effort": effort,
        "max_completion_tokens": MAX_OUTPUT_TOKENS,
        "messages": [{"role": roles[m.type], "content": m.content} for m in messages],
        "response_format": type_to_response_format_param(schema),
    }


async def submit(requests: dict[str, dict]) -> str:
    """Sends chat completion bodies keyed by custom id as one batch; returns its id."""
    lines = [
        json.dumps({"custom_id": custom_id, "method": "POST", "url": COMPLETIONS, "body": body})
        for custom_id, body in requests.items()
    ]
    upload = await get_client().files.create(
        file=("requests.jsonl", io.BytesIO("\n".join(lines).encode())), purpose="batch"
    )
    batch = await get_client().batches.create(
        input_file_id=upload.id, endpoint=COMPLETIONS, completion_window="24h"
    )

    return batch.id


async def status(batch_id: str) -> tuple[str, str | None]:
    """The batch's status and, once completed, the id of its output file."""
    batch = await get_client().batches.retrieve(batch_id)

    return batch.status, batch.output_file_id


def usage_of(body: dict) -> dict:
    """A reply's usage as LangChain reports a call's: input, cached input and output tokens."""
    usage = body.get("usage") or {}
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)

    return {
        "input_tokens": usage.get("prompt_tokens", 0),
        "output_tokens": usage.get("completion_tokens", 0),
        "input_token_details": {"cache_read": cached or 0},
    }


async def results(file_id: str) -> tuple[dict[str, str | None], list[tuple[str, str, dict]]]:
    """The reply text per custom id, None for a request that failed; and the custom id, model
    and usage of each request that reported one."""
    content = await get_client().files.content(file_id)
    replies = {}
    used = []

    for line in content.text.splitlines():
        if not line.strip():
            continue

        item = json.loads(line)
        response = item.get("response") or {}
        body = response.get("body") or {}
        choices = body.get("choices") or [{}]
        reply = choices[0].get("message", {}).get("content")
        replies[item["custom_id"]] = reply if response.get("status_code") == 200 else None

        if body.get("usage"):
            used.append((item["custom_id"], body.get("model", ""), usage_of(body)))

    return replies, used
