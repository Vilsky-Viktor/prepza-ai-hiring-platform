import uuid

from fastapi import HTTPException, status
from testee_common.ai.sets import PreparationIn

from library.core.db import Session
from library.helpers.sets import new_interview
from library.models.sets import QuestionSet, Topic
from library.repositories import bank, preparations
from library.services.set_saves import save_once


async def create_interview(payload: PreparationIn) -> uuid.UUID:
    """A company's interview, with its topics' embeddings (kept like a template's). A retried
    save from the same generation returns the set it already made."""

    async def create() -> uuid.UUID:
        async with Session.begin() as session:
            embeddings = [topic.embedding for topic in payload.topics]
            sources = [q.source_id for topic in payload.topics for q in topic.questions]
            reused = await bank.bank_ids(session, [s for s in sources if s is not None])

            return await preparations.add(session, new_interview(payload, reused), embeddings)

    return await save_once(payload.generation_id, create)


async def with_topics(set_id: uuid.UUID) -> tuple[QuestionSet, list[tuple[Topic, int]]] | None:
    """A set and its topics, each with how many questions candidates can be given."""
    async with Session() as session:
        question_set = await preparations.get(session, set_id)

        if question_set is None:
            return None

        return question_set, await preparations.get_topics(session, set_id)


async def rename(set_id: uuid.UUID, title: str) -> None:
    async with Session.begin() as session:
        if await preparations.get(session, set_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Set not found")

        await preparations.set_title(session, set_id, title)


async def delete(set_id: uuid.UUID) -> None:
    """Deletes the set; safe to repeat."""
    async with Session.begin() as session:
        if await preparations.get(session, set_id) is not None:
            await preparations.remove(session, set_id)


async def remove_interview(
    interview_id: uuid.UUID, company_id: uuid.UUID, set_id: uuid.UUID | None, generation_id
) -> None:
    """A deleted interview's questions and bank opt-out (interview.deleted); safe to repeat, so a
    redelivered event deletes nothing more. Copies of its questions in the shared bank stay:
    they hold no company id and their link to the source is only cleared."""
    async with Session.begin() as session:
        await preparations.remove_interview(session, company_id, set_id, generation_id)
        await bank.forget_interview(session, interview_id, company_id)


async def remove_company(company_id: uuid.UUID) -> None:
    """A deleted company's sets (company.deleted), a batch at a time; also one saved after its
    interview's own event came. Then its bank opt-outs. Copies of its questions in the shared
    bank stay."""
    await preparations.remove_company(Session, company_id)

    async with Session.begin() as session:
        await bank.forget_company(session, company_id)
