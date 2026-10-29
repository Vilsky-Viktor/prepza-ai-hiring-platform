"""One shape for an answer voted down, wherever it was found (disliked_answers.py): from a
Langfuse trace's model calls or from the local votes tables. No service packages, so it's tested
on the host (scripts/tests/test_disliked_answers.py)."""

import json


def disliked(source: str, trace_id: str | None, date: str, question, answer) -> dict:
    """`source` is "assistant", "help" or "unknown"; the help chat keeps no text, so locally its
    question and answer are None."""
    return {
        "source": source,
        "trace_id": trace_id,
        "date": date,
        "question": question,
        "answer": answer,
    }


def parsed(value):
    """Langfuse gives a call's input and output as JSON text."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return value

    return value


def text_of(message) -> str | None:
    """A message's text: its content as a string, or its text parts joined."""
    content = message.get("content") if isinstance(message, dict) else message

    if isinstance(content, list):
        parts = [part.get("text", "") for part in content if isinstance(part, dict)]

        return "\n".join(part for part in parts if part) or None

    return content if isinstance(content, str) and content else None


def exchange(calls: list[tuple]) -> tuple[str | None, str | None]:
    """The question and the answer of a trace from its model calls, as (start time, input,
    output): the last user message the last call read, and what the last call wrote (the
    assistant's earlier calls choose tools)."""
    if not calls:
        return None, None

    _, given, written = max(calls, key=lambda call: call[0])
    messages = parsed(given)
    asked = [m for m in messages if isinstance(m, dict) and m.get("role") in ("user", "human")]

    return (text_of(asked[-1]) if asked else None), text_of(parsed(written))
