import uuid
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common import memory_cache
from prepza_common.auth import CurrentUser
from prepza_common.limits import question_seconds
from prepza_common.multi_answer import multi_share
from prepza_common.paging import PageParams
from prepza_common.pause import refuse_if_paused
from prepza_common.rate_limit import hit_or_skip

from app.constants.practice import (
    NO_PRACTICE_QUESTIONS,
    PRACTICE_SIZE_CACHE_SECONDS,
    STANDARD_TIMING,
)
from app.helpers.practice import (
    practice_statuses,
    practice_timings,
    practice_topics,
    round_out,
    round_size,
    round_summaries,
    timing_seconds,
    topic_progress,
)
from app.integrations import library
from app.integrations.redis import get_redis
from app.schemas.practice import (
    PracticeRoundOut,
    PracticeRoundSummary,
    PracticeSizeOut,
    PracticeStartIn,
    PracticeStartOut,
    PracticeStatusOut,
    PracticeTopicProgress,
)
from app.storage import practice_sessions, sessions

# Free practice for talents: rounds on a template's revealed questions, timed as the talent
# chooses (standard, double or untimed), up to the PRACTICE_ROUNDS_PER_HOUR limit, each with
# fresh random questions and every right answer shown after.
router = APIRouter(prefix="/practice", tags=["practice"])


@router.post("/{template_id}", status_code=status.HTTP_201_CREATED)
async def start_practice(
    template_id: UUID, user: CurrentUser, body: PracticeStartIn | None = None
) -> PracticeStartOut:
    redis = get_redis()
    await refuse_if_paused(redis, "practice", user_id=user.uid)
    content = await library.practice_content(template_id)

    if content is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test not found")

    if not content["topics"]:
        raise HTTPException(status.HTTP_409_CONFLICT, NO_PRACTICE_QUESTIONS)

    # Counted once it would start, against floods: with Redis down, not counted.
    key = f"rate:practice:{user.uid}"
    await hit_or_skip(redis, key, "PRACTICE_ROUNDS_PER_HOUR", user_id=user.uid)

    round_id = uuid.uuid4()
    # Only a talent's first round counts in the questions' statistics: later rounds repeat
    # questions whose answers were shown, so they measure memory, not knowledge.
    # A round with more time or none doesn't count either: it no longer measures the same thing.
    timing = body.timing if body else STANDARD_TIMING
    repeat = await practice_sessions.practiced(user.uid, template_id)
    rows = await sessions.create_many(
        user.uid,
        round_id,
        practice_topics(content, await multi_share(redis)),
        timing_seconds(await question_seconds(redis, content["level"]), timing),
        preview=repeat or timing != STANDARD_TIMING,
        practice=True,
    )

    return PracticeStartOut(round_id=round_id, session_id=rows[0].id)


@router.get("/statuses")
async def list_statuses(user: CurrentUser) -> list[PracticeStatusOut]:
    """Where the talent is on each template they practiced, for the practice list: one entry
    a template, never started ones left out."""
    return practice_statuses(await practice_sessions.latest_round_sections(user.uid))


@router.get("/{template_id}/size")
async def practice_size(template_id: UUID) -> PracticeSizeOut:
    """Public, for the test's page: how many questions a round has (with its level, kept for a
    few minutes), and the times per question to choose from."""
    key = f"practice-size:{template_id}"
    cached = memory_cache.get(key)

    if cached is None:
        content = await library.practice_content(template_id)

        if content is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Test not found")

        cached = (round_size(content), content["level"])
        memory_cache.put(key, cached, PRACTICE_SIZE_CACHE_SECONDS)

    size, level = cached
    base = await question_seconds(get_redis(), level)

    return PracticeSizeOut(questions=size, timings=practice_timings(base))


@router.get("/rounds/{round_id}")
async def get_round(round_id: UUID, user: CurrentUser) -> PracticeRoundOut:
    """The talent's own round only."""
    rows = [
        row
        for row in await sessions.list_for_invite(round_id)
        if row.user_id == user.uid and row.practice
    ]

    if not rows:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Round not found")

    found = await library.get_set(rows[0].interview_set_id)

    title, language = (found["title"], found.get("language")) if found else (None, None)

    return round_out(rows, title, language)


@router.get("/{template_id}/rounds")
async def list_rounds(
    template_id: UUID, user: CurrentUser, page: PageParams
) -> list[PracticeRoundSummary]:
    """The talent's rounds on the template, newest first, a page at a time, to see their
    progress."""
    rows = await practice_sessions.practice_rounds(user.uid, template_id, page.offset, page.limit)

    return round_summaries(rows)


@router.get("/{template_id}/progress")
async def topic_progress_route(template_id: UUID, user: CurrentUser) -> list[PracticeTopicProgress]:
    """How far the talent got on each of the template's topics in their latest round."""
    return topic_progress(await practice_sessions.practice_rounds(user.uid, template_id, 0, 1))
