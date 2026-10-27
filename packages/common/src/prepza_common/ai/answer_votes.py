"""People's thumbs up and down on the chats' answers (the assistant's and the help chat's) sent
to Langfuse as a score on the answer's trace (prepza_common.ai.tracing), only when Langfuse is set
up. The vote itself is saved by the service first; this only mirrors it. Needs the package's
`langfuse` extra."""

import asyncio
import logging
from collections.abc import Awaitable, Callable

from langfuse.api import CreateScoreRequest
from langfuse.api.core.api_error import ApiError
from prepza_common.ai import tracing
from prepza_common.http.backoff import wait_seconds

logger = logging.getLogger(__name__)

# The score's name in Langfuse; its value is 1 for a thumbs up, 0 for a thumbs down.
VOTE_SCORE = "user_vote"
UP = 1
DOWN = -1
# A vote is mirrored inside its own request, which waits for it at most SEND_SECONDS: nothing runs
# after the answer (Cloud Run throttles the CPU then, so a background send stalls or is lost), and
# a slow Langfuse never holds the request longer. Tried SEND_ATTEMPTS times, after a jittered wait
# from FIRST_WAIT_SECONDS; Langfuse's client doesn't retry on its own (one layer of retries).
SEND_ATTEMPTS = 2
FIRST_WAIT_SECONDS = 0.5
SEND_SECONDS = 3
ONE_TRY = {"max_retries": 0, "timeout_in_seconds": SEND_SECONDS}


def score_id(trace_id: str) -> str:
    """One vote score a trace: a changed vote replaces it, a cleared one deletes it."""
    return f"{trace_id}-{VOTE_SCORE}"


def _mirror(trace_id: str, vote: int | None) -> None:
    scores = tracing.client().api.scores
    found = score_id(trace_id)

    if vote is None:
        try:
            scores.delete(found, request_options=ONE_TRY)
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
    result = scores.create(request=[score], request_options=ONE_TRY)

    if getattr(result, "errors", None):
        raise RuntimeError("Langfuse refused the score")


async def send_vote(trace_id: str, current: Callable[[], Awaitable[int | None]]) -> None:
    """Mirrors the answer's vote as it is when sent (`current` reads it), and again if it changed
    meanwhile, so quick changes on any instance end with the latest; retried, then logged and
    dropped (the vote stays saved by the service)."""
    sent = object()

    for attempt in range(SEND_ATTEMPTS):
        try:
            vote = await current()

            if vote == sent:
                return

            await asyncio.to_thread(_mirror, trace_id, vote)
            sent = vote

            if await current() == vote:
                return
        except Exception as error:  # noqa: BLE001 - logged by its type only
            logger.warning(
                "Couldn't send a vote to Langfuse (try %d): %s",
                attempt + 1,
                type(error).__name__,
            )

            if attempt + 1 < SEND_ATTEMPTS:
                await asyncio.sleep(wait_seconds(FIRST_WAIT_SECONDS, attempt))


async def mirror_vote(trace_id: str | None, current: Callable[[], Awaitable[int | None]]) -> None:
    """Sends the vote within SEND_SECONDS; nothing when the answer has no trace or Langfuse isn't
    set up."""
    if trace_id is None or not tracing.tracing_on():
        return

    try:
        async with asyncio.timeout(SEND_SECONDS):
            await send_vote(trace_id, current)
    except TimeoutError:
        logger.warning("Couldn't send a vote to Langfuse in time")
