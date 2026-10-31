from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from testee_common.auth.auth import CurrentUser
from testee_common.db.paging import PageParams
from testee_common.limits.limits import question_seconds
from testee_common.redis import memory_cache

from rounds.constants.practice import PRACTICE_SIZE_CACHE_SECONDS, STANDARD_TIMING
from rounds.core.db import Session
from rounds.helpers.practice import (
    practice_statuses,
    practice_timings,
    round_out,
    round_summaries,
    topic_progress,
    topic_sizes,
)
from rounds.integrations import library
from rounds.integrations.redis import get_redis
from rounds.repositories import practice_sessions, sessions
from rounds.schemas.practice import (
    PracticeRoundOut,
    PracticeRoundSummary,
    PracticeSizeOut,
    PracticeStartIn,
    PracticeStartOut,
    PracticeStatusOut,
    PracticeTopicProgress,
)
from rounds.services import practice

# Free practice for talents: rounds on a template's revealed questions, timed as the talent
# chooses (standard, double or untimed), up to the PRACTICE_ROUNDS_PER_HOUR limit, each with
# fresh random questions and every right answer shown after.
router = APIRouter(prefix="/practice", tags=["practice"])


@router.post("/{template_id}", status_code=status.HTTP_201_CREATED)
async def start_practice(
    template_id: UUID, user: CurrentUser, body: PracticeStartIn | None = None
) -> PracticeStartOut:
    return await practice.start(template_id, user.uid, body.timing if body else STANDARD_TIMING)


@router.get("/statuses")
async def list_statuses(user: CurrentUser) -> list[PracticeStatusOut]:
    """Where the talent is on each template they practiced, for the practice list: one entry
    a template, never started ones left out."""
    async with Session() as session:
        rows = await practice_sessions.latest_rounds(session, user.uid)

    return practice_statuses(rows)


@router.get("/{template_id}/size")
async def practice_size(template_id: UUID) -> PracticeSizeOut:
    """Public, for the test's page: how many questions a round has, in all and on each topic
    (with its level, kept for a few minutes), and the times per question to choose from."""
    key = f"practice-size:{template_id}"
    cached = memory_cache.get(key)

    if cached is None:
        content = await library.practice_content(template_id)

        if content is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Test not found")

        cached = (topic_sizes(content), content["level"])
        memory_cache.put(key, cached, PRACTICE_SIZE_CACHE_SECONDS)

    topics, level = cached
    base = await question_seconds(get_redis(), level)

    return PracticeSizeOut(
        questions=sum(topics.values()), topics=topics, timings=practice_timings(base)
    )


@router.get("/rounds/{round_id}")
async def get_round(round_id: UUID, user: CurrentUser) -> PracticeRoundOut:
    """The talent's own round only."""
    async with Session() as session:
        found = await sessions.list_for_invite(session, round_id)

    rows = [row for row in found if row.user_id == user.uid and row.practice]

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
    async with Session() as session:
        rows = await practice_sessions.practice_rounds(
            session, user.uid, template_id, page.offset, page.limit
        )

    return round_summaries(rows)


@router.get("/{template_id}/progress")
async def topic_progress_route(template_id: UUID, user: CurrentUser) -> list[PracticeTopicProgress]:
    """How far the talent got on each of the template's topics in their latest round."""
    async with Session() as session:
        rows = await practice_sessions.practice_rounds(session, user.uid, template_id, 0, 1)

    return topic_progress(rows)
