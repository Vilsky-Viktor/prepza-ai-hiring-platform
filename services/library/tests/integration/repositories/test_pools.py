import uuid

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from testee_common.ai.sets import TopicAdditionIn

from library.constants.sets import Pool
from library.core.db import Session
from library.repositories import pools, preparations
from library.services import questions as question_service
from tests.integration.factories import COPYABLE, a_company, copy_of, interview
from tests.integration.transactions import transaction

OPTIONS = [{"answer": "right", "correct": True}, {"answer": "wrong", "correct": False}]


def new(*texts):
    return [{"text": text, "options": OPTIONS} for text in texts]


def test_added_questions_go_after_the_last_into_their_pools_and_reach_only_new_copies(run):
    async def scenario():
        template = await interview("Addition", template=True, questions=COPYABLE)
        older_copy = await copy_of(template, a_company("add"))
        [topic] = (await transaction(preparations.get_content, template)).topics
        ids = await transaction(
            pools.add_questions,
            template,
            [TopicAdditionIn(topic_id=topic.id, practice=new("P1?"), company=new("C1?", "C2?"))],
        )
        foreign = await transaction(
            pools.add_questions,
            template,
            [TopicAdditionIn(topic_id=uuid.uuid4(), practice=new("X?"), company=[])],
        )
        after = (await transaction(preparations.get_content, template)).topics[0].questions
        newer_copy = await copy_of(template, a_company("add"))

        return (
            ids,
            foreign,
            after,
            await transaction(preparations.get_topics, older_copy.id),
            await transaction(preparations.get_topics, newer_copy.id),
            await transaction(pools.topic_counts, template),
        )

    ids, foreign, after, older, newer, counts = run(scenario())

    assert [question.id for question in after[-3:]] == ids[0]
    assert [(q.text, q.pool, q.position) for q in after[-3:]] == [
        ("P1?", "practice", COPYABLE),
        ("C1?", "company", COPYABLE + 1),
        ("C2?", "company", COPYABLE + 2),
    ]
    assert foreign is None
    assert [count for _, count in older] == [10]
    assert [count for _, count in newer] == [12]
    assert [(practice, company) for _, practice, company in counts] == [(31, 12)]


def test_a_fixed_question_keeps_its_pool(run):
    async def scenario():
        template = await interview("Fixed pool", template=True, questions=COPYABLE)
        questions = (await transaction(preparations.get_content, template)).topics[0].questions
        practice, company = questions[0], questions[-1]

        for question in (practice, company):
            await question_service.replace(question.id, f"Clearer {question.id}?", OPTIONS)

        after = (await transaction(preparations.get_content, template)).topics[0].questions

        return after[0].pool, after[-1].pool

    assert run(scenario()) == (Pool.PRACTICE, Pool.COMPANY)


def test_the_migration_puts_revealed_questions_in_practice_and_the_rest_in_company(run):
    async def setup():
        template = await interview("Migrated", template=True, questions=3)
        company_test = await interview("Migrated company test", questions=1)
        [topic] = (await transaction(preparations.get_content, template)).topics
        stages = ["private", "retiring", "revealed"]

        async with Session() as session:
            for question, stage in zip(topic.questions, stages):
                await session.execute(
                    text("UPDATE questions SET stage = :stage WHERE id = :id"),
                    {"stage": stage, "id": question.id},
                )

            await session.commit()

        return template, company_test

    async def pools_of(set_id):
        async with Session() as session:
            rows = await session.execute(
                text(
                    "SELECT q.pool FROM questions q JOIN topics t ON t.id = q.topic_id "
                    "WHERE t.set_id = :id ORDER BY q.position"
                ),
                {"id": set_id},
            )

            return [row[0] for row in rows]

    template, company_test = run(setup())
    config = Config("alembic.ini")
    command.downgrade(config, "0026")
    command.upgrade(config, "head")

    assert run(pools_of(template)) == ["company", "company", "practice"]
    assert run(pools_of(company_test)) == [None]
