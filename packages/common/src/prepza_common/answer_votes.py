"""The chats' answers (the assistant's and the help chat's) traced to Langfuse, and people's thumbs
up and down on them sent there as a score on the answer's trace. On only when
LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are set (LANGFUSE_HOST: Langfuse's EU cloud unless
set). The vote itself is saved by the service first; this only mirrors it. Needs the package's
`langfuse` extra."""

import asyncio
import logging
import os
from collections.abc import Awaitable, Callable
from functools import cache

from langfuse import Langfuse
from langfuse.api import CreateScoreRequest
from langfuse.api.core.api_error import ApiError
from langfuse.langchain import CallbackHandler

logger = logging.getLogger(__name__)

EU_CLOUD = "https://cloud.langfuse.com"
# The score's name in Langfuse; its value is 1 for a thumbs up, 0 for a thumbs down.
VOTE_SCORE = "user_vote"
UP = 1
DOWN = -1
# Tries to send a vote, waiting twice as long after each failure.
SEND_ATTEMPTS = 4
FIRST_WAIT_SECONDS = 2

# Votes being sent, kept so they aren't collected mid-send; one at a time an answer (its lock,
# kept for the process's life: votes are few), so a quick change of mind can't be overtaken by
# the vote before it.
_sending: set[asyncio.Task] = set()
_locks: dict[str, asyncio.Lock] = {}


def tracing_on() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


@cache
def _client() -> Langfuse:
    return Langfuse(
        public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
        secret_key=os.environ["LANGFUSE_SECRET_KEY"],
        host=os.getenv("LANGFUSE_HOST") or EU_CLOUD,
    )


def new_trace_id() -> str | None:
    """A new answer's Langfuse trace, which its model calls report to and a vote scores; None
    when Langfuse isn't set up."""
    if not tracing_on():
        return None

    return _client().create_trace_id()


def traced(trace_id: str | None) -> dict | None:
    """The config a model call reports to the answer's trace with; None without one."""
    if trace_id is None:
        return None

    # The handler reports through the client made with these keys.
    _client()
    handler = CallbackHandler(
        public_key=os.environ["LANGFUSE_PUBLIC_KEY"], trace_context={"trace_id": trace_id}
    )

    return {"callbacks": [handler]}


def score_id(trace_id: str) -> str:
    """One vote score a trace: a changed vote replaces it, a cleared one deletes it."""
    return f"{trace_id}-{VOTE_SCORE}"


def _mirror(trace_id: str, vote: int | None) -> None:
    scores = _client().api.scores
    found = score_id(trace_id)

    if vote is None:
        try:
            scores.delete(found)
        except ApiError as error:
            if error.status_code != 404:
                raise

        return

    score = CreateScoreRequest(
        id=found,
        trace_id=trace_id,
        name=VOTE_SCORE,
        value=1 if vote == UP else 0,
        data_type="NUMERIC",
    )
    result = scores.create(request=[score])

    if getattr(result, "errors", None):
        raise RuntimeError("Langfuse refused the score")


async def send_vote(trace_id: str, current: Callable[[], Awaitable[int | None]]) -> None:
    """Mirrors the answer's vote as it is when sent (`current` reads it), so retries and quick
    changes end with the latest; retried with backoff, then logged and dropped (the vote stays
    saved by the service)."""
    async with _locks.setdefault(trace_id, asyncio.Lock()):
        for attempt in range(SEND_ATTEMPTS):
            try:
                await asyncio.to_thread(_mirror, trace_id, await current())

                return
            except Exception as error:  # noqa: BLE001 - logged by its type only
                logger.warning(
                    "Couldn't send a vote to Langfuse (try %d): %s",
                    attempt + 1,
                    type(error).__name__,
                )

                if attempt + 1 < SEND_ATTEMPTS:
                    await asyncio.sleep(FIRST_WAIT_SECONDS * 2**attempt)


def mirror_vote(trace_id: str | None, current: Callable[[], Awaitable[int | None]]) -> None:
    """Sends the vote in the background; nothing when the answer has no trace or Langfuse isn't
    set up."""
    if trace_id is None or not tracing_on():
        return

    task = asyncio.create_task(send_vote(trace_id, current))
    _sending.add(task)
    task.add_done_callback(_sending.discard)
