import logging
import math

import httpx
from prepza_common.ai.multi_answer import draw

from app.constants.interviews import (
    DEFAULT_TOPIC_QUESTIONS,
    GENERATION_FAILED_STATUS,
    InterviewStatus,
)
from app.integrations import generation as generation_api
from app.integrations import library
from app.models.interviews import Interview
from app.schemas.interviews import InterviewOut, TopicOut
from app.storage import candidates, interview_generations, interviews

logger = logging.getLogger(__name__)


async def attach_set(interview: Interview) -> Interview:
    """Asks generation once, for a route about this one interview, in case its
    generation.completed or generation.failed hasn't come yet. Lists never ask: they show what
    those events stored."""
    if interview.set_id:
        return interview

    row = await generation_api.get(interview.generation_id, interview.company_id)
    set_id = row.get("preparation_id") if row else None

    if set_id:
        await interview_generations.set_set_id(interview.id, set_id)
        interview.set_id = set_id
        interview.generation_failed = False

        return interview

    failed = bool(row) and row.get("status") == GENERATION_FAILED_STATUS

    if failed != interview.generation_failed:
        await interview_generations.set_generation_failed(interview.id, failed)
        interview.generation_failed = failed

    return interview


async def attach_set_if_reachable(interview: Interview) -> Interview:
    """attach_set for an interview's own page: with generation down, the page shows what
    companies knows instead of failing."""
    try:
        return await attach_set(interview)
    except httpx.HTTPError:
        logger.warning("Generation unreachable; interview %s shown as stored", interview.id)

        return interview


async def interview_title(interview: Interview) -> str | None:
    """The stored title. Interviews finished before titles were stored fetch it once."""
    if interview.title or not interview.set_id:
        return interview.title

    found = await library.get_set(interview.set_id)

    if found:
        await interviews.set_title(interview.id, found["title"])
        interview.title = found["title"]

    return interview.title


def interview_status(hired: bool, candidate_count: int) -> InterviewStatus:
    if hired:
        return InterviewStatus.HIRED

    return InterviewStatus.IN_PROCESS if candidate_count else InterviewStatus.NEW


async def interview_out(interview: Interview, candidate_count: int = 0) -> InterviewOut:
    title = await interview_title(interview)

    return InterviewOut(
        id=interview.id,
        generation_id=interview.generation_id,
        set_id=interview.set_id,
        generation_failed=interview.generation_failed,
        title=title,
        question_seconds=interview.question_seconds,
        candidate_count=candidate_count,
        hired=interview.hired,
        pass_mark=interview.pass_mark,
        link_token=interview.link_token,
        status=interview_status(interview.hired, candidate_count),
        created_at=interview.created_at,
        updated_at=interview.updated_at,
    )


async def interviews_page(company_id, offset: int, limit: int, q: str = "") -> list[InterviewOut]:
    """A page of the company's interviews, newest first, each with how many candidates it has;
    `q` narrows them to titles containing it."""
    rows = await interviews.list_for_company(company_id, offset, limit, q=q)
    totals = await candidates.counts([item.id for item in rows])

    return [await interview_out(item, totals.get(item.id, 0)) for item in rows]


def topic_limit(limits: dict[str, int], topic_id) -> int:
    """Questions a candidate gets from the topic: the manager's number, or the default."""
    return limits.get(str(topic_id), DEFAULT_TOPIC_QUESTIONS)


def topics_out(found: dict, limits: dict[str, int]) -> list[TopicOut]:
    return [
        TopicOut(
            id=topic["id"],
            title=topic["title"],
            subtopics=topic.get("subtopics", []),
            question_count=topic["question_count"],
            question_limit=min(topic_limit(limits, topic["id"]), topic["question_count"]),
        )
        for topic in found.get("topics", [])
    ]


def interview_questions(found: dict | None, limits: dict[str, int]) -> int | None:
    """Every question a candidate gets, over all topics. None while the interview's questions
    aren't known."""
    if not found:
        return None

    return sum(topic.question_limit for topic in topics_out(found, limits))


def interview_minutes(found: dict | None, limits: dict[str, int], seconds: int) -> int | None:
    """The whole interview's time, in minutes rounded up: every question a candidate gets at
    `seconds` each. None while the interview's questions aren't known."""
    questions = interview_questions(found, limits)

    if questions is None:
        return None

    return math.ceil(questions * seconds / 60)


def pick_questions(questions: list, limit: int, share: float) -> list:
    """Each candidate gets a fresh random subset with `share` of multi-answer questions
    (prepza_common.ai.multi_answer.draw), or every question when the topic has no more."""
    if limit >= len(questions):
        return questions

    return draw(questions, limit, share)


def session_topics(interview: Interview, content: dict, share: float) -> list[dict]:
    """Each topic with a fresh random subset of its questions, as rounds starts sessions. A topic
    set to 0 questions is left out: the candidate never sees it, and it never counts."""
    return [
        {
            "id": topic["id"],
            "preparation_id": content["id"],
            "title": topic["title"],
            "questions": pick_questions(
                topic["questions"], topic_limit(interview.topic_limits, topic["id"]), share
            ),
        }
        for topic in content["topics"]
        if topic_limit(interview.topic_limits, topic["id"]) > 0
    ]
