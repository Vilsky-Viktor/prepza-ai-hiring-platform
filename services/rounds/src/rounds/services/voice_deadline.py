import logging
import math
from datetime import UTC, datetime, timedelta
from uuid import UUID

from redis.exceptions import RedisError

from rounds.constants.rounds import TIME_GRACE_SECONDS
from rounds.constants.voice import IN_TIME_KEY, VOICE_ANSWER_GRACE_SECONDS, VOICE_UPLOAD_SECONDS
from rounds.helpers.sessions import question_deadline
from rounds.integrations.redis import get_redis
from rounds.models.sessions import Session

logger = logging.getLogger(__name__)


async def note_arrival(row: Session, question_id: UUID) -> None:
    """A spoken answer to the question on screen reached the service: by its deadline (and the
    upload's margin), it's noted, so the answer it gives counts a little past the deadline
    (answer_grace). The time is the service's own, never the browser's. A note that can't be
    saved leaves the usual grace."""
    deadline = question_deadline(row)
    now = datetime.now(UTC)

    if deadline is None or now > deadline + timedelta(seconds=VOICE_UPLOAD_SECONDS):
        return

    ends = deadline + timedelta(seconds=VOICE_ANSWER_GRACE_SECONDS)
    seconds = max(1, math.ceil((ends - now).total_seconds()))

    try:
        await get_redis().set(IN_TIME_KEY.format(session_id=row.id), str(question_id), ex=seconds)
    except RedisError as error:
        logger.warning("A voice answer's arrival wasn't noted: %s", type(error).__name__)


async def answer_grace(session_id: UUID, question_id: UUID) -> int:
    """Seconds past the deadline an answer to `question_id` may still arrive: longer when a
    spoken answer to it reached the service in time (note_arrival), the usual grace otherwise."""
    try:
        noted = await get_redis().get(IN_TIME_KEY.format(session_id=session_id))
    except RedisError:
        return TIME_GRACE_SECONDS

    if noted is not None and noted.decode() == str(question_id):
        return VOICE_ANSWER_GRACE_SECONDS

    return TIME_GRACE_SECONDS
