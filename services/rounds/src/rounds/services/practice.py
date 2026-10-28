import uuid
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from prepza_common.ai.multi_answer import multi_share
from prepza_common.limits.limits import question_seconds
from prepza_common.limits.pause import refuse_if_paused
from prepza_common.limits.rate_limit import hit_or_skip

from rounds.constants.practice import NO_PRACTICE_QUESTIONS, STANDARD_TIMING
from rounds.core.db import Session
from rounds.helpers.practice import practice_topics, timing_seconds
from rounds.helpers.sessions import new_sections
from rounds.integrations import library
from rounds.integrations.redis import get_redis
from rounds.repositories import practice_sessions, sessions
from rounds.schemas.practice import PracticeStartOut


async def start(template_id: UUID, user_id: str, timing: str) -> PracticeStartOut:
    """A talent's free practice round on a template's revealed questions, timed as they chose,
    up to the PRACTICE_ROUNDS_PER_HOUR limit, with fresh random questions."""
    redis = get_redis()
    await refuse_if_paused(redis, "practice", user_id=user_id)
    content = await library.practice_content(template_id)

    if content is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test not found")

    if not content["topics"]:
        raise HTTPException(status.HTTP_409_CONFLICT, NO_PRACTICE_QUESTIONS)

    # Counted once it would start, against floods: with Redis down, not counted.
    await hit_or_skip(
        redis, f"rate:practice:{user_id}", "PRACTICE_ROUNDS_PER_HOUR", user_id=user_id
    )
    topics = practice_topics(content, await multi_share(redis))
    seconds = timing_seconds(await question_seconds(redis, content["level"]), timing)
    round_id = uuid.uuid4()

    async with Session.begin() as session:
        # Only a talent's first round counts in the questions' statistics: later rounds repeat
        # questions whose answers were shown, so they measure memory, not knowledge. A round
        # with more time or none doesn't count either: it no longer measures the same thing.
        repeat = await practice_sessions.practiced(session, user_id, template_id)
        rows = new_sections(
            user_id,
            round_id,
            topics,
            seconds,
            datetime.now(UTC),
            preview=repeat or timing != STANDARD_TIMING,
            practice=True,
        )
        await sessions.add_all(session, rows)

    return PracticeStartOut(round_id=round_id, session_id=rows[0].id)
