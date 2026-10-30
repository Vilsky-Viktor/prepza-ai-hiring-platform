import uuid
from datetime import UTC, datetime

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User

from companies.constants.invites import EMAIL_NOT_VERIFIED, NO_PLEDGE, InviteStatus
from companies.main import app
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import invites as invite_store

INVITE_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()


def sign_in(email, verified=True, uid="cand"):
    app.dependency_overrides[current_user] = lambda: User(
        uid=uid, email=email, email_verified=verified, name="Bob"
    )


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def stored_invite(monkeypatch):
    invite = CandidateInvite(
        id=INVITE_ID,
        interview_id=INTERVIEW_ID,
        email="bob@example.com",
        token="token-1",
        status=InviteStatus.INVITED,
        created_at=datetime.now(UTC),
        guest=False,
    )
    interview = Interview(
        id=INTERVIEW_ID,
        company_id=uuid.uuid4(),
        generation_id=uuid.uuid4(),
        set_id=uuid.uuid4(),
        topic_limits={},
    )

    async def fake_get(session, token):
        return (invite, interview) if token == "token-1" else None

    monkeypatch.setattr(invite_store, "get_by_token", fake_get)

    return invite


@pytest.mark.parametrize(
    ("email", "verified", "detail"),
    [
        ("eve@example.com", True, "This invite was sent to a different email address"),
        # Their own email, not verified yet (GitHub): told to confirm it, not that it's another.
        ("bob@example.com", False, EMAIL_NOT_VERIFIED),
    ],
)
def test_other_or_unverified_email_is_rejected(client, stored_invite, email, verified, detail):
    sign_in(email, verified)
    response = client.post("/invites/token-1/start")

    assert response.status_code == 403
    assert response.json()["detail"] == detail


@pytest.fixture
def starts(monkeypatch, stored_invite):
    """The candidates whose sessions were started."""
    from companies.services import candidate_start

    started = []

    async def start(invite, interview, user):
        started.append(user.uid)

        return {"sessions": []}

    monkeypatch.setattr(candidate_start, "start_sessions", start)

    return started


@pytest.mark.parametrize("body", [None, {}, {"pledged": False}])
def test_a_first_start_needs_the_candidates_pledge(client, starts, body):
    """To answer on their own, without AI tools or other people: the page asks for it, and the
    API holds every other client to it."""
    sign_in("bob@example.com")
    response = client.post("/invites/token-1/start", json=body)

    assert response.status_code == 422
    assert response.json()["detail"] == NO_PLEDGE
    assert starts == []


def test_a_pledged_candidate_starts(client, starts):
    sign_in("bob@example.com")

    assert client.post("/invites/token-1/start", json={"pledged": True}).status_code == 200
    assert starts == ["cand"]


def test_a_candidate_already_in_the_interview_continues_without_pledging_again(
    client, starts, stored_invite
):
    stored_invite.status = InviteStatus.IN_PROCESS
    sign_in("bob@example.com")

    assert client.post("/invites/token-1/start").status_code == 200
    assert starts == ["cand"]


def test_unknown_token(client, stored_invite):
    sign_in("bob@example.com")

    assert client.post("/invites/missing/start").status_code == 404


@pytest.fixture
def invite_page(monkeypatch, stored_invite):
    """What the invitation page reads besides the invite: its interview and company."""
    from companies.services import invite_pages as pages

    async def same(interview):
        interview.question_seconds = 60

        return interview

    async def title(interview):
        return "Backend"

    async def company(session, company_id):
        return None

    async def found_set(set_id):
        return {"topics": [{"id": str(uuid.uuid4()), "title": "Python", "question_count": 4}]}

    monkeypatch.setattr(pages, "attach_set", same)
    monkeypatch.setattr(pages, "interview_title", title)
    monkeypatch.setattr(pages.companies, "get", company)
    monkeypatch.setattr(pages.set_cache, "get_set", found_set)

    return stored_invite


def test_a_visitor_sees_the_invitation_without_the_candidates_email(client, invite_page):
    """Before signing in, the page shows what the invite is for; whose it is, only after."""
    response = client.get("/invites/token-1")

    assert response.status_code == 200
    assert response.json()["title"] == "Backend"
    assert response.json()["email"] is None
    # The set's 4 questions at 60 seconds each, answered by clicks.
    assert response.json()["total_minutes"] == 4
    assert response.json()["voice"] is False


@pytest.mark.parametrize(
    ("email", "verified", "matches", "shown"),
    [
        ("Bob@Example.com", True, True, "bob@example.com"),
        # Their address, not confirmed yet: told it's theirs, never shown it.
        ("bob@example.com", False, True, None),
        # Anyone else with the link: neither.
        ("eve@example.com", True, False, None),
    ],
)
def test_only_the_verified_account_it_was_sent_to_sees_its_address(
    client, invite_page, email, verified, matches, shown
):
    from prepza_common.auth.auth import optional_user

    app.dependency_overrides[optional_user] = lambda: User(
        uid="cand", email=email, email_verified=verified, name="Bob"
    )

    found = client.get("/invites/token-1").json()

    assert (found["matches"], found["email"]) == (matches, shown)
