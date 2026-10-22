import uuid
from datetime import UTC, datetime

import httpx
import pytest
from fake_redis import FakeRedis
from prepza_common.audit_actions import AuditAction, TargetKind
from prepza_common.auth import current_user
from prepza_common.user import User

import app.routers.interview_generation as generation_routes
from app.integrations import generation
from app.main import app
from app.models.companies import Company, Member
from app.models.interviews import Interview
from app.storage import companies, interview_generations, interviews

COMPANY_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()
GENERATION_ID = uuid.uuid4()
# A generation as the generation service returns it, waiting for its topics to be reviewed.
GENERATION = {
    "id": str(GENERATION_ID),
    "kind": "interview",
    "company_id": str(COMPANY_ID),
    "status": "awaiting_review",
    "topics": [{"main_topic": "Python", "subtopics": ["Typing", "Async"]}],
    "progress": {"done": 0, "total": 10, "topics": 1, "topics_ready": 0},
    "preparation_id": None,
    "error": None,
    "language": "en",
    "max_topics": 5,
    "max_subtopics": 6,
}


def sign_in(uid):
    app.dependency_overrides[current_user] = lambda: User(
        uid=uid, email=f"{uid}@example.com", email_verified=True, name=uid
    )


def setup(monkeypatch, role):
    interview = Interview(
        id=INTERVIEW_ID,
        company_id=COMPANY_ID,
        generation_id=GENERATION_ID,
        set_id=None,
    )
    company = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC))
    company.members = [
        Member(
            company_id=COMPANY_ID, user_id="alice", invited_email="alice@example.com", role="owner"
        ),
        Member(company_id=COMPANY_ID, user_id="bob", invited_email="bob@example.com", role=role),
    ]

    async def fake_interview(_interview_id):
        return interview

    async def fake_company(_company_id):
        return company

    monkeypatch.setattr(interviews, "get", fake_interview)
    monkeypatch.setattr(companies, "get", fake_company)


def test_admin_who_did_not_start_it_sees_the_generation(client, monkeypatch):
    """The generation belongs to alice, but bob is in the same company."""
    setup(monkeypatch, "admin")
    sign_in("bob")
    calls = []

    async def fake_get(generation_id, company_id):
        calls.append((generation_id, company_id))

        return GENERATION

    monkeypatch.setattr(generation, "get", fake_get)
    response = client.get(f"/interviews/{INTERVIEW_ID}/generation")

    assert response.status_code == 200
    assert response.json() == GENERATION
    assert calls == [(GENERATION_ID, COMPANY_ID)]

    app.dependency_overrides.clear()


def test_outsider_does_not_see_the_generation(client, monkeypatch):
    setup(monkeypatch, "admin")
    sign_in("mallory")

    assert client.get(f"/interviews/{INTERVIEW_ID}/generation").status_code == 404

    app.dependency_overrides.clear()


def test_only_managers_review_topics(client, monkeypatch, audited):
    sign_in("bob")
    calls = []

    async def fake_review(generation_id, company_id, body):
        calls.append(body)

        return httpx.Response(
            200,
            json={"id": str(generation_id), "status": "queued"},
            request=httpx.Request("POST", "http://generation"),
        )

    monkeypatch.setattr(generation, "review", fake_review)
    url = f"/interviews/{INTERVIEW_ID}/generation/review"
    body = {"selected": [0, 2], "instructions": ""}

    for role, expected in (("viewer", 403), ("admin", 200)):
        setup(monkeypatch, role)

        assert client.post(url, json=body).status_code == expected

    # Without hand edits the topics go through as null; generation then keeps its draft.
    assert calls == [{**body, "topics": None}]
    assert audited == [
        (COMPANY_ID, "bob", AuditAction.TOPICS_APPROVED, INTERVIEW_ID, TargetKind.INTERVIEW)
    ]

    app.dependency_overrides.clear()


def test_second_review_passes_the_conflict_through(client, monkeypatch, audited):
    setup(monkeypatch, "admin")
    sign_in("bob")

    async def fake_review(generation_id, company_id, body):
        return httpx.Response(409, json={"detail": "Generation is not awaiting review"})

    monkeypatch.setattr(generation, "review", fake_review)
    response = client.post(f"/interviews/{INTERVIEW_ID}/generation/review", json={"selected": [0]})

    assert response.status_code == 409
    assert response.json()["detail"] == "Generation is not awaiting review"
    assert audited == []

    app.dependency_overrides.clear()


@pytest.mark.parametrize(("code", "retry_after"), [(429, "3600"), (503, "7200")])
def test_a_review_generation_refuses_reaches_the_user_with_its_wait(
    client, monkeypatch, audited, code, retry_after
):
    """Its topic revisions used up (429) or the day's AI budget (503): never a 500."""
    setup(monkeypatch, "admin")
    sign_in("bob")

    async def fake_review(generation_id, company_id, body):
        headers = {"Retry-After": retry_after}

        return httpx.Response(code, json={"detail": "Not now"}, headers=headers)

    monkeypatch.setattr(generation, "review", fake_review)
    response = client.post(f"/interviews/{INTERVIEW_ID}/generation/review", json={"selected": [0]})

    assert (response.status_code, response.json()["detail"]) == (code, "Not now")
    assert response.headers["Retry-After"] == retry_after
    assert audited == []

    app.dependency_overrides.clear()


def test_only_managers_retry_and_a_retry_clears_the_failure(client, monkeypatch):
    sign_in("bob")
    calls = []
    cleared = []

    async def set_generation_failed(interview_id, failed):
        cleared.append((interview_id, failed))

    async def fake_retry(generation_id, company_id):
        calls.append(generation_id)

        return httpx.Response(
            200,
            json={"id": str(generation_id), "status": "queued"},
            request=httpx.Request("POST", "http://generation"),
        )

    monkeypatch.setattr(generation, "retry", fake_retry)
    redis = FakeRedis({"GENERATION_RETRIES_PER_COMPANY_DAY": 1})
    monkeypatch.setattr(generation_routes, "get_redis", lambda: redis)
    url = f"/interviews/{INTERVIEW_ID}/generation/retry"

    for role, expected in (("viewer", 403), ("admin", 200)):
        setup(monkeypatch, role)
        monkeypatch.setattr(interview_generations, "set_generation_failed", set_generation_failed)

        assert client.post(url).status_code == expected

    assert calls == [GENERATION_ID]
    assert cleared == [(INTERVIEW_ID, False)]
    # The company's runs again a day: the next is refused before generation hears of it.
    assert client.post(url).status_code == 429
    assert calls == [GENERATION_ID]

    app.dependency_overrides.clear()


def test_only_managers_cancel_and_the_interview_goes_with_it(client, monkeypatch):
    sign_in("bob")
    removed = []

    async def fake_cancel(generation_id, company_id):
        return httpx.Response(
            200,
            json={"id": str(generation_id), "status": "cancelled"},
            request=httpx.Request("POST", "http://generation"),
        )

    async def fake_remove(interview_id):
        removed.append(interview_id)

    monkeypatch.setattr(generation, "cancel", fake_cancel)
    monkeypatch.setattr(interviews, "remove", fake_remove)
    url = f"/interviews/{INTERVIEW_ID}/generation/cancel"

    for role, expected in (("viewer", 403), ("admin", 200)):
        setup(monkeypatch, role)

        assert client.post(url).status_code == expected

    assert removed == [INTERVIEW_ID]

    app.dependency_overrides.clear()


def test_a_finished_generation_keeps_its_interview(client, monkeypatch):
    setup(monkeypatch, "admin")
    sign_in("bob")
    removed = []

    async def fake_cancel(generation_id, company_id):
        return httpx.Response(409, json={"detail": "Generation already finished"})

    async def fake_remove(interview_id):
        removed.append(interview_id)

    monkeypatch.setattr(generation, "cancel", fake_cancel)
    monkeypatch.setattr(interviews, "remove", fake_remove)

    assert client.post(f"/interviews/{INTERVIEW_ID}/generation/cancel").status_code == 409
    assert removed == []

    app.dependency_overrides.clear()
