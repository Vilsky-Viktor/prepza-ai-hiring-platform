"""The admin zone's quality tab, and the verifier's look at one question."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from testee_common.limits.pause import refuse_if_paused

from library.constants.sets import SetKind
from library.core.db import Session
from library.integrations import generation
from library.integrations.redis import get_redis
from library.models.feedback import QuestionReport
from library.models.quality import QuestionStats
from library.models.sets import Question
from library.repositories import feedback, preparations, quality
from library.services.quality import mark_wrong


async def with_reports(
    question_id: uuid.UUID,
) -> tuple[Question, QuestionStats | None, list[QuestionReport]] | None:
    """The question, its answer stats and every report; None when it's gone."""
    async with Session() as session:
        found = await quality.load(session, question_id)

        if found is None:
            return None

        return found[0], found[1], await feedback.list_reports(session, question_id)


async def template_flag(session: AsyncSession, question_id: uuid.UUID) -> str:
    """A flagged question in a template, or not found; its flag."""
    question_set = await preparations.get_for_question(session, question_id)
    found = await quality.load(session, question_id)

    if question_set is None or question_set.kind != SetKind.TEMPLATE or found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")

    stats = found[1]

    if stats is None or stats.flag is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Question isn't flagged")

    return stats.flag


async def fix_now(question_id: uuid.UUID, superadmin_id: str) -> None:
    """Sends the question to the verifier at once; it fixes or replaces it in the background."""
    await refuse_if_paused(get_redis(), "question_fix", user_id=superadmin_id)

    async with Session() as session:
        flag = await template_flag(session, question_id)

    await generation.verify_question(question_id, flag, now=True)


async def dismiss(question_id: uuid.UUID) -> None:
    """The flag is wrong: the question stays, and isn't flagged again until it changes."""
    async with Session.begin() as session:
        await template_flag(session, question_id)
        await quality.save_flag(session, question_id, None, kept=True)


async def mark_template_wrong(template_id: uuid.UUID, question_id: uuid.UUID) -> None:
    """A superadmin says a template question's marked answer is wrong (quality.mark_wrong)."""
    async with Session() as session:
        template = await preparations.get_for_question(session, question_id)

    if template is None or template.id != template_id or template.kind != SetKind.TEMPLATE:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")

    await mark_wrong(question_id)
