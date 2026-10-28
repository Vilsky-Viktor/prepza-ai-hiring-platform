import uuid
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User

from companies.constants.invites import NO_PLEDGE
from companies.integrations import library, rounds
from companies.main import app
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.repositories import companies, interviews
from companies.services import previews as interview_routes

COMPANY_ID = uuid.uuid4()
SET_ID = uuid.uuid4()
SESSION_ID = uuid.uuid4()


@pytest.fixture
def started(monkeypatch):
    """Bob, a viewer of the company, and one ready test; returns the previews counted (their
    keys) and what rounds was asked for."""
    asked = []
    company = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC))
    company.members = [
        Member(
            company_id=COMPANY_ID,
            user_id="bob",
            invited_email="bob@example.com",
            role="viewer",
            created_at=datetime.now(UTC),
        )
    ]

    def interview(set_id=SET_ID):
        return Interview(
            id=uuid.uuid4(),
            company_id=COMPANY_ID,
            generation_id=None,
            set_id=set_id,
            question_seconds=45,
            topic_limits={},
        )

    async def get_interview(session, _interview_id):
        return interview()

    async def get_company(session, _company_id):
        return company

    async def content(_set_id):
        questions = [{"id": str(uuid.uuid4()), "text": "Q?", "options": []} for _ in range(3)]

        return {"id": str(SET_ID), "topics": [{"id": "t1", "title": "SQL", "questions": questions}]}

    async def create_sessions(payload):
        asked.append(payload)

        return [{"id": str(SESSION_ID), "topic_title": "SQL", "status": "in_progress"}]

    async def counted(redis, key, name, **whose):
        asked.append(key)

    monkeypatch.setattr(interview_routes, "hit_or_skip", counted)
    monkeypatch.setattr(interviews, "get", get_interview)
    monkeypatch.setattr(companies, "get", get_company)
    monkeypatch.setattr(library, "get_content", content)
    monkeypatch.setattr(rounds, "create_sessions", create_sessions)
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True
    )

    yield asked

    app.dependency_overrides.clear()


def test_any_member_previews_a_test_as_a_candidate_would_for_free(client, started):
    response = client.post(f"/interviews/{uuid.uuid4()}/preview", json={"pledged": True})

    assert response.status_code == 201
    assert response.json() == {"session_id": str(SESSION_ID)}
    [counted, payload] = started
    assert counted == "rate:previews:bob"
    # Marked as a preview, timed like the real test, and with no invite behind it to charge.
    assert payload["preview"] is True
    assert payload["question_seconds"] == 45
    assert payload["user_id"] == "bob"
    assert len(payload["topics"][0]["questions"]) == 3


def test_a_preview_starts_with_the_pledge_as_a_candidates_start_does(client, started):
    response = client.post(f"/interviews/{uuid.uuid4()}/preview")

    assert response.status_code == 422
    assert response.json()["detail"] == NO_PLEDGE
    # Neither counted toward the hourly limit nor started.
    assert started == []


def test_someone_outside_the_company_cant(client, started):
    app.dependency_overrides[current_user] = lambda: User(
        uid="eve", email="eve@example.com", email_verified=True
    )

    assert (
        client.post(f"/interviews/{uuid.uuid4()}/preview", json={"pledged": True}).status_code
        == 404
    )
    assert started == []


def test_previews_over_the_hourly_limit_are_refused(client, started, monkeypatch):
    async def over(redis, key, name, **whose):
        raise HTTPException(429, "Too many requests. Try again later.")

    monkeypatch.setattr(interview_routes, "hit_or_skip", over)

    assert (
        client.post(f"/interviews/{uuid.uuid4()}/preview", json={"pledged": True}).status_code
        == 429
    )
    assert started == []
