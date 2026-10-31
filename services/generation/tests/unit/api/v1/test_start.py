import uuid

import pytest
from testee_common.config.constants import LANGUAGES

from generation.models.generation import Generation
from generation.repositories import generations
from tests.unit.api.v1.test_internal_generations import headers

COMPANY_ID = uuid.uuid4()


@pytest.fixture
def queue(monkeypatch):
    """Generations that are recorded, not run."""
    created = []

    async def fake_create(
        session, owner_uid, text, company_id=None, language="en", generation_id=None
    ):
        created.append((owner_uid, company_id, language))

        return Generation(
            id=uuid.uuid4(),
            owner_uid=owner_uid,
            text=text,
            kind="interview",
            company_id=company_id,
            status="queued",
            language=language,
        )

    monkeypatch.setattr(generations, "create", fake_create)

    return created


def start(client, **body):
    return client.post(
        "/internal/generations",
        json={"text": "Backend engineer", "company_id": str(COMPANY_ID), "owner_uid": "bob"} | body,
        headers=headers(),
    )


def test_a_test_is_written_in_its_texts_language_not_the_interfaces(client, queue):
    # A recruiter with a Russian interface, hiring for an English-speaking role.
    response = start(client, language="ru")

    assert response.status_code == 201
    assert response.json()["language"] == "en"
    assert queue == [("bob", COMPANY_ID, "en")]


def test_a_recruiter_can_choose_the_tests_language(client, queue):
    response = start(client, generate_in="ar")

    assert response.json()["language"] == "ar"


def test_only_supported_languages_can_be_chosen(client, queue):
    response = start(client, generate_in="xx")

    assert response.status_code == 422
    assert queue == []


def test_the_languages_to_generate_in_are_listed(client):
    languages = client.get("/languages").json()

    assert languages[0] == "en"
    assert languages == list(LANGUAGES)
