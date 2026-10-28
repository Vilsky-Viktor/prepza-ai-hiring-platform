"""A company's set and everything under it carry the company, a template none; and one topic or
question per place, checked when the transaction ends, so a reorder can swap two."""

import uuid

import pytest
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from library.core.db import Session
from library.models.sets import Question, QuestionSet, Topic
from library.repositories import preparations
from tests.integration.factories import interview
from tests.integration.transactions import transaction


def companies_of(set_id):
    async def read():
        async with Session() as session:
            owner = await session.scalar(
                select(QuestionSet.company_id).where(QuestionSet.id == set_id)
            )
            topics = set(
                await session.scalars(select(Topic.company_id).where(Topic.set_id == set_id))
            )
            questions = set(
                await session.scalars(
                    select(Question.company_id).join(Topic).where(Topic.set_id == set_id)
                )
            )

        return owner, topics, questions

    return read()


def test_a_companys_set_and_its_rows_carry_the_company_a_templates_none(run):
    owner = str(uuid.uuid4())

    async def scenario():
        own = await interview(owner=owner)
        template = await interview(template=True)

        return await companies_of(own), await companies_of(template)

    own, template = run(scenario())

    company = uuid.UUID(owner)
    assert own == (company, {company}, {company})
    assert template == (None, {None}, {None})


def test_two_questions_swap_places_but_cant_share_one(run):
    async def scenario():
        set_id = await interview(questions=2)
        first, second = (await transaction(preparations.get_content, set_id)).topics[0].questions

        async with Session() as session:
            await session.execute(
                update(Question).where(Question.id == first.id).values(position=1)
            )
            await session.execute(
                update(Question).where(Question.id == second.id).values(position=0)
            )
            await session.commit()

        async with Session() as session:
            await session.execute(
                update(Question).where(Question.id == second.id).values(position=1)
            )

            with pytest.raises(IntegrityError) as refused:
                await session.commit()

        return refused.value.orig.diag.constraint_name

    assert run(scenario()) == "uq_questions_topic_position"
