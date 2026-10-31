import uuid
from datetime import UTC, datetime

import httpx
from testee_common.auth.auth import current_user
from testee_common.auth.user import User
from testee_common.http import http

from companies.integrations import billing, rounds
from companies.main import app
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import companies, interviews, invites

COMPANY_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()
SET_ID = uuid.uuid4()
URL = f"/interviews/{INTERVIEW_ID}"


def setup(monkeypatch, role, set_id=SET_ID):
    """Records the deletion's steps in order; bob has the given role. Every other service
    answers 503, as if rounds and library were down: the deletion calls none of them."""
    calls = []

    def down(request):
        calls.append(("call", request.url.host))

        return httpx.Response(503)

    client = httpx.AsyncClient(transport=httpx.MockTransport(down))
    monkeypatch.setattr(http, "get_client", lambda: client)
    interview = Interview(
        id=INTERVIEW_ID,
        company_id=COMPANY_ID,
        generation_id=uuid.uuid4(),
        set_id=set_id,
        generation_failed=False,
    )
    company = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC))
    company.members = [
        Member(company_id=COMPANY_ID, user_id="bob", invited_email="bob@example.com", role=role),
    ]

    async def fake_interview(session, _interview_id):
        return interview

    async def fake_company(session, _company_id):
        return company

    async def fake_remove(session, interview_id):
        calls.append(("interview", interview_id))

        return []

    monkeypatch.setattr(interviews, "get", fake_interview)
    monkeypatch.setattr(companies, "get", fake_company)
    monkeypatch.setattr(interviews, "remove", fake_remove)
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True, name="bob"
    )

    return calls


def test_deletes_the_interview_while_rounds_and_library_are_down(client, monkeypatch):
    """Their data goes with interview.deleted (saved with the interview's removal), so the
    deletion waits on neither."""
    calls = setup(monkeypatch, "admin")

    assert client.delete(URL).status_code == 204
    assert calls == [("interview", INTERVIEW_ID)]

    app.dependency_overrides.clear()


def test_viewers_cannot_delete(client, monkeypatch):
    calls = setup(monkeypatch, "viewer")

    assert client.delete(URL).status_code == 403
    assert calls == []

    app.dependency_overrides.clear()


def test_an_interview_still_generating_is_cancelled_instead(client, monkeypatch):
    calls = setup(monkeypatch, "admin", set_id=None)

    async def no_generation(_generation_id, _company_id):
        return None

    monkeypatch.setattr("companies.services.interview_views.generation_api.get", no_generation)

    assert client.delete(URL).status_code == 409
    assert calls == []

    app.dependency_overrides.clear()


def candidate(email, status):
    return CandidateInvite(
        id=uuid.uuid4(),
        interview_id=INTERVIEW_ID,
        email=email,
        status=status,
        hold_key=f"{INTERVIEW_ID}:{email.split('@')[0]}-key",
    )


def test_deleting_an_interview_settles_unfinished_candidates_credits(client, monkeypatch):
    """Charged for one who answered something, given back for the rest, before the interview
    (and with its event, rounds' answers) goes."""
    calls = setup(monkeypatch, "admin")
    carol = candidate("carol@example.com", "invited")
    dan = candidate("dan@example.com", "in_process")
    erin = candidate("erin@example.com", "in_process")

    async def unfinished(session, interview_id, after, size):
        return [carol, dan, erin] if after is None else []

    async def scores(invite_ids):
        calls.append(("scores", sorted(invite_ids)))

        # Erin's questions so far all ran out of time: not an answer.
        return {
            str(dan.id): {"progress": 20, "picked": 1},
            str(erin.id): {"progress": 20, "picked": 0},
        }

    async def release(key):
        calls.append(("release", key))

    async def charge(key):
        calls.append(("charge", key))

    monkeypatch.setattr(invites, "unfinished", unfinished)
    monkeypatch.setattr(rounds, "invite_scores", scores)
    monkeypatch.setattr(billing, "release_candidate", release)
    monkeypatch.setattr(billing, "charge_candidate", charge)

    assert client.delete(URL).status_code == 204
    assert calls == [
        ("scores", sorted([dan.id, erin.id])),
        ("release", f"{INTERVIEW_ID}:carol-key"),
        ("charge", f"{INTERVIEW_ID}:dan-key"),
        ("release", f"{INTERVIEW_ID}:erin-key"),
        ("interview", INTERVIEW_ID),
    ]

    app.dependency_overrides.clear()


def test_an_invite_made_while_the_interview_is_deleted_gives_its_credits_back(client, monkeypatch):
    setup(monkeypatch, "admin")
    released = []

    async def remove(session, interview_id):
        return [(INTERVIEW_ID, "late@example.com", "invited", "late-key")]

    async def release(key):
        released.append(key)

    monkeypatch.setattr(interviews, "remove", remove)
    monkeypatch.setattr(billing, "release_candidate", release)

    assert client.delete(URL).status_code == 204
    assert released == ["late-key"]

    app.dependency_overrides.clear()
