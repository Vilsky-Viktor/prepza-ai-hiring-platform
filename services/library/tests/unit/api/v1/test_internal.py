import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
from prepza_common.http.http import bearer

from library.constants.sets import SetKind
from library.models.sets import QuestionSet
from library.repositories import preparations, templates

GENERATION_ID = uuid.uuid4()
PAYLOAD = {
    "generation_id": str(GENERATION_ID),
    "owner_uid": "user-1",
    "source_text": "Job",
    "title": "Backend",
    "level": "medium",
    "requirements": ["Python"],
    "topics": [],
}


def token(secret="test-secret-that-is-at-least-32-bytes", lifetime=60):
    exp = datetime.now(UTC) + timedelta(seconds=lifetime)

    return jwt.encode(
        {"iss": "generation", "aud": "library", "exp": exp}, secret, algorithm="HS256"
    )


def post(client, value):
    return client.post("/internal/interviews", json=PAYLOAD, headers=bearer(value))


def test_create_with_service_token(client, monkeypatch):
    new_id = uuid.uuid4()

    async def fake_find(generation_id):
        return None

    async def fake_create(payload):
        return new_id

    monkeypatch.setattr(preparations, "find_by_generation", fake_find)
    monkeypatch.setattr(preparations, "create_interview", fake_create)

    response = post(client, token())

    assert response.status_code == 201
    assert response.json() == {"id": str(new_id)}


def test_retried_interview_save_returns_the_existing_set(client, monkeypatch):
    existing_id = uuid.uuid4()

    async def fake_find(generation_id):
        assert generation_id == GENERATION_ID

        return existing_id

    async def fail_create(payload):
        raise AssertionError("must not create a second set")

    monkeypatch.setattr(preparations, "find_by_generation", fake_find)
    monkeypatch.setattr(preparations, "create_interview", fail_create)

    response = client.post(
        "/internal/interviews",
        json=PAYLOAD,
        headers=bearer(token()),
    )

    assert response.json() == {"id": str(existing_id)}


def interview_delete(client, monkeypatch, kind):
    removed = []

    async def fake_get(set_id):
        return None if kind is None else QuestionSet(id=set_id, kind=kind)

    async def fake_remove(set_id):
        removed.append(set_id)

    monkeypatch.setattr(preparations, "get", fake_get)
    monkeypatch.setattr(preparations, "remove", fake_remove)
    response = client.delete(
        f"/internal/interviews/{GENERATION_ID}",
        headers=bearer(token()),
    )

    return response.status_code, removed


def test_companies_deletes_an_interview_set(client, monkeypatch):
    assert interview_delete(client, monkeypatch, SetKind.INTERVIEW) == (204, [GENERATION_ID])


def test_deleting_a_missing_interview_set_succeeds(client, monkeypatch):
    assert interview_delete(client, monkeypatch, None) == (204, [])


def test_rejects_wrong_secret(client):
    assert post(client, token(secret="another-secret-that-is-32-bytes-long")).status_code == 401


def test_rejects_expired_token(client):
    assert post(client, token(lifetime=-10)).status_code == 401


def test_a_template_copy_carries_its_level_for_the_tests_seconds_a_question(client, monkeypatch):
    copy = SimpleNamespace(id=uuid.uuid4(), title="Backend", language="de", level="hard")

    async def copy_template(template_id, company_id):
        return copy

    monkeypatch.setattr(templates, "copy_template", copy_template)

    response = client.post(
        f"/internal/templates/{uuid.uuid4()}/copy",
        json={"company_id": "company-1"},
        headers=bearer(token()),
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": str(copy.id),
        "title": "Backend",
        "language": "de",
        "level": "hard",
    }
