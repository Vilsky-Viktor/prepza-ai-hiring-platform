import uuid
from datetime import UTC, datetime

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User

from companies.api.v1 import invites as invites_router
from companies.constants.invites import InviteStatus
from companies.integrations import library, rounds
from companies.main import app
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import invite_progress
from companies.repositories import invites as invite_store


@pytest.fixture(autouse=True)
def candidate():
    app.dependency_overrides[current_user] = lambda: User(
        uid="cand", email="bob@example.com", email_verified=True
    )
    yield
    app.dependency_overrides.clear()


def start(client, monkeypatch):
    invite = CandidateInvite(
        id=uuid.uuid4(),
        interview_id=uuid.uuid4(),
        email="bob@example.com",
        token="token-1",
        status=InviteStatus.INVITED,
        created_at=datetime.now(UTC),
    )
    interview = Interview(
        id=invite.interview_id,
        company_id=uuid.uuid4(),
        generation_id=uuid.uuid4(),
        set_id=uuid.uuid4(),
        question_seconds=45,
        topic_limits={},
    )
    sent = {}

    async def fake_get(token):
        return invite, interview

    async def same(item):
        return item

    async def fake_content(set_id):
        return {
            "id": str(set_id),
            "topics": [{"id": str(uuid.uuid4()), "title": "T", "questions": []}],
        }

    async def fake_start(invite_id, user_id, name=None):
        return True

    async def fake_create(payload):
        sent.update(payload)

        return []

    monkeypatch.setattr(invite_store, "get_by_token", fake_get)
    monkeypatch.setattr(invites_router, "attach_set", same)
    monkeypatch.setattr(library, "get_content", fake_content)
    monkeypatch.setattr(invite_progress, "start", fake_start)
    monkeypatch.setattr(rounds, "create_sessions", fake_create)

    assert client.post("/invites/token-1/start", json={"pledged": True}).status_code == 200

    return sent


def test_every_interview_limits_each_question(client, monkeypatch):
    sent = start(client, monkeypatch)

    assert sent["question_seconds"] == 45
    # Candidates never see their scores, so there's nothing to share.
    assert "share_results" not in sent
