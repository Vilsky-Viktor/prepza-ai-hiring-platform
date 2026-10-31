"""Saving a generation's set: two saves at once, of one generation or of two templates with the
same title, each end with one set, without an error."""

import asyncio
import uuid

from testee_common.ai.sets import PreparationIn

from library.repositories import preparations
from library.services import sets as set_service
from library.services import templates as template_service
from library.services.set_saves import save_once
from tests.integration.factories import a_company
from tests.integration.transactions import transaction


def payload(generation_id: uuid.UUID, title: str) -> PreparationIn:
    return PreparationIn.model_validate(
        {
            "generation_id": str(generation_id),
            "owner_uid": a_company("1"),
            "source_text": "job text",
            "title": title,
            "level": "medium",
            "language": "en",
            "requirements": [],
            "topics": [
                {
                    "title": "Python",
                    "subtopics": [],
                    "embedding": None,
                    "questions": [
                        {
                            "text": f"{title} question?",
                            "options": [
                                {"answer": "right", "correct": True},
                                {"answer": "wrong", "correct": False},
                            ],
                        }
                    ],
                }
            ],
        }
    )


def test_two_saves_of_one_generation_at_once_return_one_set(run):
    generation_id = uuid.uuid4()
    body = payload(generation_id, f"Backend {uuid.uuid4().hex[:6]}")

    async def scenario():
        return await asyncio.gather(*(set_service.create_interview(body) for _ in range(2)))

    first, second = run(scenario())

    assert first == second


def test_two_templates_of_one_title_at_once_each_get_a_slug(run):
    title = f"Nurse {uuid.uuid4().hex[:6]}"
    bodies = [payload(uuid.uuid4(), title) for _ in range(2)]

    def creator(body):
        async def create():
            return await template_service.save_template(body, 0.1)

        return create

    async def scenario():
        made = await asyncio.gather(*(save_once(b.generation_id, creator(b)) for b in bodies))

        return [(await transaction(preparations.get, set_id)).slug for set_id in made]

    slugs = run(scenario())

    assert len(set(slugs)) == 2
