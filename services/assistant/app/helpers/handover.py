from langchain_core.messages import ToolMessage

from app.constants.chat import HANDOVER, HANDOVER_FAILURES
from app.models.tools import ToolResult


def failed_on_our_side(result: ToolResult) -> bool:
    """A call that failed through no fault of its arguments: a service that didn't answer or
    answered with an error of its own."""
    if result.status_code is None:
        return result.content.get("error") in (503, 504)

    return result.status_code >= 500


def with_handover(replies: list[ToolMessage], before: list[ToolResult], now: list[ToolResult]):
    """The step's replies, the last one telling the model to hand the user over to a person
    once the turn's calls have failed HANDOVER_FAILURES times (told once)."""
    failed_before = sum(failed_on_our_side(result) for result in before)
    failed = failed_before + sum(failed_on_our_side(result) for result in now)

    if not replies or failed_before >= HANDOVER_FAILURES or failed < HANDOVER_FAILURES:
        return replies

    last = replies[-1]
    note = f"{last.content}\n\n{HANDOVER}"

    return [*replies[:-1], last.model_copy(update={"content": note})]
