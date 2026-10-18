"""People's thumbs up and down on the chats' answers (the assistant's and the help chat's) sent
to Langfuse as a score on the answer's trace (prepza_common.tracing), only when Langfuse is set
up. The vote itself is saved by the service first; this only mirrors it. Needs the package's
`langfuse` extra."""

import asyncio
import logging
from collections.abc import Awaitable, Callable

from langfuse.api import CreateScoreRequest
from langfuse.api.core.api_error import ApiError
from prepza_common import tracing

logger = logging.getLogger(__name__)

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


def score_id(trace_id: str) -> str:
    """One vote score a trace: a changed vote replaces it, a cleared one deletes it."""
    return f"{trace_id}-{VOTE_SCORE}"


def _mirror(trace_id: str, vote: int | None) -> None:
    scores = tracing.client().api.scores
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
    if trace_id is None or not tracing.tracing_on():
        return

    task = asyncio.create_task(send_vote(trace_id, current))
    _sending.add(task)
    task.add_done_callback(_sending.discard)
