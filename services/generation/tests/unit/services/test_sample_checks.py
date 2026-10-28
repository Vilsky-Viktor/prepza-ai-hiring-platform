import asyncio
import uuid

from generation.integrations import library
from generation.services import sample_checks


def test_one_random_key_a_topic_is_checked_and_a_failure_never_raises(monkeypatch):
    topics = [[uuid.uuid4() for _ in range(5)], [uuid.uuid4() for _ in range(3)], []]
    checked = []

    async def question_ids(_set_id):
        return topics

    async def check_one(question_id):
        checked.append(question_id)

        if question_id in topics[1]:
            raise RuntimeError("verifier down")

    monkeypatch.setattr(library, "get_question_ids", question_ids)
    monkeypatch.setattr(sample_checks, "check_one", check_one)

    asyncio.run(sample_checks.check_sample(uuid.uuid4()))

    # One from each topic that has questions; the failing one didn't stop the rest.
    assert len(checked) == 2
    assert checked[0] in topics[0] and checked[1] in topics[1]


def test_a_library_outage_doesnt_fail_the_generation(monkeypatch):
    async def down(_set_id):
        raise ConnectionError("library is down")

    monkeypatch.setattr(library, "get_question_ids", down)

    asyncio.run(sample_checks.check_sample(uuid.uuid4()))
