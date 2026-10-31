import uuid

from fastapi import HTTPException
from testee_common.ai.sets import PreparationIn

from library.repositories import preparations
from library.services import sets as set_service
from library.services import templates as template_service
from tests.integration.transactions import transaction

DIMENSIONS = 256
# A new template's first 30 fresh questions of a topic go to practice: with 40, a topic has 10
# company questions, as many as a copy needs (MIN_COPY_QUESTIONS).
COPYABLE = 40


def a_company(name: str) -> str:
    """A company's id for a test's name of it: a uuid (sets.owner_id holds one), the same for the
    same name."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"company-{name}"))


def direction(*values: float) -> list[float]:
    """A unit vector of the embedding's size, pointing along `values`."""
    length = sum(value * value for value in values) ** 0.5

    return [value / length for value in values] + [0.0] * (DIMENSIONS - len(values))


async def interview(
    title="Backend",
    topic="Python",
    subtopics=(),
    level="medium",
    embedding=None,
    questions=3,
    language="en",
    owner=None,
    template=False,
    topic_embeddings=None,
):
    """A company's test set (of `owner`, by default a_company("1")), or a template, with one topic
    of `questions` questions, or one topic per embedding in `topic_embeddings`."""
    owner = owner or a_company("1")
    payload = PreparationIn.model_validate(
        {
            "generation_id": str(uuid.uuid4()),
            "owner_uid": owner,
            "source_text": "job text",
            "title": title,
            "level": level,
            "language": language,
            "requirements": [],
            "topics": [
                {
                    "title": f"{topic} {number}" if topic_embeddings else topic,
                    "subtopics": list(subtopics),
                    "embedding": topic_embedding,
                    "questions": [
                        {
                            "text": f"{title} question {index}?",
                            "options": [
                                {"answer": "right", "correct": True},
                                {"answer": "wrong", "correct": False},
                            ],
                        }
                        for index in range(questions)
                    ],
                }
                for number, topic_embedding in enumerate(topic_embeddings or [embedding])
            ],
        }
    )

    if template:
        return await template_service.save_template(payload, 0.1)

    return await set_service.create_interview(payload)


async def copy_of(template_id, company_id):
    """A company's test copied from a template, as companies asks for one; None when the
    template can't be copied (the service answers 404)."""
    try:
        return await template_service.copy_template(template_id, company_id)
    except HTTPException:
        return None


async def question_ids(set_id):
    content = await transaction(preparations.get_content, set_id)

    return [question.id for topic in content.topics for question in topic.questions]


async def set_pool(question_ids, pool):
    """Puts questions in another pool, as the migration did for older templates' stages; the
    service itself never moves a question."""
    from sqlalchemy import update

    from library.core.db import Session
    from library.models.sets import Question

    async with Session() as session:
        await session.execute(
            update(Question).where(Question.id.in_(question_ids)).values(pool=pool)
        )
        await session.commit()
