import uuid

import pytest
from prepza_common.http.http import bearer
from pydantic import ValidationError

from app.constants.generation import MAX_INSTRUCTIONS_LENGTH, RUN_GENERATION
from app.models.generation import Generation
from app.routers import internal
from app.schemas.generation import ReviewRequest
from app.service_auth import service_token
from app.storage import generations

COMPANY_ID = uuid.uuid4()
GENERATION_ID = uuid.uuid4()


def headers():
    return bearer(service_token("generation"))


def company_generation():
    return Generation(
        id=GENERATION_ID,
        owner_uid="alice",
        kind="interview",
        company_id=COMPANY_ID,
        text="Job description",
        language="en",
        status="awaiting_review",
        topics=[{"main_topic": "Python", "subtopics": ["asyncio"]}],
        progress=None,
        preparation_id=None,
        error=None,
    )


def fake_get(monkeypatch):
    async def get(_generation_id):
        return company_generation()

    monkeypatch.setattr(generations, "get", get)


def test_company_generation_is_visible_to_its_company(client, monkeypatch):
    fake_get(monkeypatch)
    response = client.get(
        f"/internal/generations/{GENERATION_ID}",
        params={"company_id": str(COMPANY_ID)},
        headers=headers(),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "awaiting_review"


def test_company_generation_is_hidden_from_another_company(client, monkeypatch):
    fake_get(monkeypatch)
    response = client.get(
        f"/internal/generations/{GENERATION_ID}",
        params={"company_id": str(uuid.uuid4())},
        headers=headers(),
    )

    assert response.status_code == 404


def test_internal_generation_needs_a_service_token(client):
    response = client.get(
        f"/internal/generations/{GENERATION_ID}", params={"company_id": str(COMPANY_ID)}
    )

    assert response.status_code in (401, 403)


def test_company_review_queues_the_topics(client, monkeypatch):
    fake_get(monkeypatch)
    reviewed = []

    async def fake_submit(generation, body):
        reviewed.append(body.selected)
        generation.status = "queued"

        return generation

    monkeypatch.setattr(internal, "submit_review", fake_submit)
    response = client.post(
        f"/internal/generations/{GENERATION_ID}/review",
        params={"company_id": str(COMPANY_ID)},
        json={"selected": [0], "instructions": ""},
        headers=headers(),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    assert reviewed == [[0]]


def test_only_a_failed_generation_is_retried(client, monkeypatch, queued):
    fake_get(monkeypatch)
    claims = iter([True, False])

    async def fake_claim(_generation_id):
        return next(claims)

    monkeypatch.setattr(generations, "claim_retry", fake_claim)
    url = f"/internal/generations/{GENERATION_ID}/retry"
    params = {"company_id": str(COMPANY_ID)}

    assert client.post(url, params=params, headers=headers()).status_code == 200
    assert client.post(url, params=params, headers=headers()).status_code == 409
    assert queued == [(RUN_GENERATION, {"generation_id": str(GENERATION_ID)})]


def drafted(monkeypatch, count):
    """A generation awaiting review with `count` drafted topics."""
    generation = company_generation()
    generation.topics = [{"main_topic": f"Topic {i}", "subtopics": []} for i in range(count)]

    async def get(_generation_id):
        return generation

    monkeypatch.setattr(generations, "get", get)


@pytest.mark.parametrize(("edited", "most"), [({}, 10), ({"MAX_TOPICS": "4"}, 4)])
def test_approving_more_than_max_topics_is_rejected(client, monkeypatch, redis, edited, most):
    """MAX_TOPICS as set in Controls now."""
    drafted(monkeypatch, 12)
    redis.limits.update(edited)
    url = f"/internal/generations/{GENERATION_ID}/review"
    params = {"company_id": str(COMPANY_ID)}

    approve = client.post(
        url,
        params=params,
        json={"selected": list(range(most + 1)), "instructions": ""},
        headers=headers(),
    )

    assert approve.status_code == 422
    assert approve.json()["detail"] == f"Choose at most {most} topics"


@pytest.mark.parametrize(("edited", "most"), [({}, 5), ({"MAX_SUBTOPICS": "2"}, 2)])
def test_a_topic_edited_with_more_than_max_subtopics_is_rejected(
    client, monkeypatch, redis, edited, most
):
    """MAX_SUBTOPICS as set in Controls now."""
    drafted(monkeypatch, 1)
    redis.limits.update(edited)
    topic = {"main_topic": "SQL", "subtopics": [f"S{i}" for i in range(most + 1)]}

    response = client.post(
        f"/internal/generations/{GENERATION_ID}/review",
        params={"company_id": str(COMPANY_ID)},
        json={"selected": [0], "instructions": "", "topics": [topic]},
        headers=headers(),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == f"A topic can have at most {most} subtopics"


def test_the_review_page_is_told_the_caps_set_in_controls(client, monkeypatch, redis):
    fake_get(monkeypatch)
    redis.limits.update({"MAX_TOPICS": "6", "MAX_SUBTOPICS": "3"})

    response = client.get(
        f"/internal/generations/{GENERATION_ID}",
        params={"company_id": str(COMPANY_ID)},
        headers=headers(),
    )

    assert (response.json()["max_topics"], response.json()["max_subtopics"]) == (6, 3)


def test_more_than_max_topics_is_fine_with_instructions_to_revise(client, monkeypatch):
    fake_get(monkeypatch)
    revised = []

    async def fake_submit(generation, body):
        revised.append(len(body.selected))

        return generation

    monkeypatch.setattr(internal, "submit_review", fake_submit)
    response = client.post(
        f"/internal/generations/{GENERATION_ID}/review",
        params={"company_id": str(COMPANY_ID)},
        json={"selected": list(range(11)), "instructions": "Merge the two SQL topics"},
        headers=headers(),
    )

    assert response.status_code == 200
    assert response.json()["max_topics"] == 10
    assert revised == [11]


def test_company_cancels_its_interview_generation(client, monkeypatch):
    generation = company_generation()

    async def get(_generation_id):
        return generation

    async def fake_cancel(_generation_id):
        generation.status = "cancelled"

        return True

    monkeypatch.setattr(generations, "get", get)
    monkeypatch.setattr(generations, "cancel", fake_cancel)
    url = f"/internal/generations/{GENERATION_ID}/cancel"

    other = client.post(url, params={"company_id": str(uuid.uuid4())}, headers=headers())
    own = client.post(url, params={"company_id": str(COMPANY_ID)}, headers=headers())

    assert other.status_code == 404
    assert own.status_code == 200
    assert own.json()["status"] == "cancelled"


def test_a_blank_edited_topic_is_rejected():
    with pytest.raises(ValidationError):
        ReviewRequest(selected=[0], topics=[{"main_topic": "  ", "subtopics": []}])

    review = ReviewRequest(selected=[0], topics=[{"main_topic": " SQL ", "subtopics": [" Joins "]}])

    assert review.topics[0].model_dump() == {"main_topic": "SQL", "subtopics": ["Joins"]}


def test_review_instructions_are_capped():
    with pytest.raises(ValidationError):
        ReviewRequest(selected=[0], instructions="x" * (MAX_INSTRUCTIONS_LENGTH + 1))

    assert ReviewRequest(selected=[0], instructions="x" * MAX_INSTRUCTIONS_LENGTH)
