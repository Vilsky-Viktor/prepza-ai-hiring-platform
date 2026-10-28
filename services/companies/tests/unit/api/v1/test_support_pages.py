"""The admin zone's support pages of an account, a candidate and an interview: superadmins
only, the database, rounds, billing, library and accounts faked. Never a candidate's questions or
answers."""

import logging
import uuid
from datetime import UTC, datetime

import pytest

from companies.integrations import accounts, billing, library, rounds
from companies.models.companies import Company
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import candidates, companies, superadmin_support

NOW = datetime(2026, 10, 1, tzinfo=UTC)
ACME = Company(id=uuid.uuid4(), name="Acme")
INTERVIEW = Interview(
    id=uuid.uuid4(),
    company_id=ACME.id,
    set_id=uuid.uuid4(),
    title="Backend",
    generation_id=uuid.uuid4(),
    generation_failed=False,
    question_seconds=60,
    pass_mark=70,
    hired=False,
    link_token=None,
    created_at=NOW,
)
ZOE = {"user_id": "uid-zoe", "email": "zoe@example.com", "created_at": "2026-09-01T00:00:00Z"}
TOP_UP = {
    "transaction_id": "txn_01",
    "company_id": str(ACME.id),
    "total": "5000",
    "currency": "USD",
    "created_at": "2026-10-02T00:00:00Z",
}
SCORES = {"finished": True, "grade": 80, "tab_leaves": 2, "copies": 1, "fast_answers": 3}


def invite(**fields) -> CandidateInvite:
    return CandidateInvite(
        **{
            "id": uuid.uuid4(),
            "interview_id": INTERVIEW.id,
            "email": "cid@example.com",
            "name": "Cid",
            "token": "token",
            "status": "finished",
            "grade": 80,
            "flagged": True,
            "extra_time": 25,
            "hold_key": "key-1",
            "created_at": NOW,
            "updated_at": NOW,
            "sent_at": NOW,
            "started_at": NOW,
            "finished_at": NOW,
            **fields,
        }
    )


CID = invite()


@pytest.fixture(autouse=True)
def stored(monkeypatch, stored_candidates):
    """Zoe owns Acme and paid for one top-up; Cid finished Acme's interview."""
    stored_candidates.add(CID)

    async def account(user_id):
        return ZOE if user_id == ZOE["user_id"] else None

    async def companies_of_user(session, user_id, limit):
        return [(ACME, "owner")] if user_id in ("uid-zoe", "uid-gone") else []

    async def buyer_purchases(user_id):
        return [TOP_UP] if user_id == "uid-zoe" else []

    async def names(session, company_ids):
        return {str(ACME.id): "Acme"}

    async def candidate(session, invite_id):
        return (CID, INTERVIEW, ACME) if invite_id == CID.id else None

    async def interview(session, interview_id):
        return (INTERVIEW, ACME) if interview_id == INTERVIEW.id else None

    async def invite_scores(invite_ids):
        return {str(CID.id): SCORES}

    async def candidate_hold(key):
        return "charged" if key == CID.hold_key else None

    async def get_set(set_id):
        return {"title": "Backend", "topics": [{"title": "Python"}, {"title": "SQL"}]}

    async def page(session, interview_id, offset, limit, by_grade, *args):
        return [CID] if not by_grade else []

    monkeypatch.setattr(accounts, "account", account)
    monkeypatch.setattr(superadmin_support, "companies_of_user", companies_of_user)
    monkeypatch.setattr(billing, "buyer_purchases", buyer_purchases)
    monkeypatch.setattr(companies, "names", names)
    monkeypatch.setattr(superadmin_support, "candidate", candidate)
    monkeypatch.setattr(superadmin_support, "interview", interview)
    monkeypatch.setattr(rounds, "invite_scores", invite_scores)
    monkeypatch.setattr(billing, "candidate_hold", candidate_hold)
    monkeypatch.setattr(library, "get_set", get_set)
    monkeypatch.setattr(candidates, "page", page)


PATHS = (
    "/superadmin/support/users/uid-zoe",
    f"/superadmin/support/candidates/{CID.id}",
    f"/superadmin/support/interviews/{INTERVIEW.id}",
    f"/superadmin/support/interviews/{INTERVIEW.id}/candidates",
)


def test_everyone_but_a_superadmin_finds_no_support_pages(client, superadmin):
    superadmin("bob@example.com")

    assert [client.get(path).status_code for path in PATHS] == [404] * len(PATHS)


def test_a_superadmin_sees_an_accounts_companies_and_top_ups(client, superadmin, caplog):
    superadmin("ann@example.com")

    with caplog.at_level(logging.INFO):
        response = client.get("/superadmin/support/users/uid-zoe")

    assert response.json() == {
        "user_id": "uid-zoe",
        "email": "zoe@example.com",
        "created_at": "2026-09-01T00:00:00Z",
        "companies": [{"id": str(ACME.id), "name": "Acme", "role": "owner"}],
        "top_ups": [{**TOP_UP, "company_name": "Acme"}],
    }
    assert "user uid-zoe viewed by superadmin" in caplog.text
    assert "zoe@example.com" not in caplog.text


def test_a_gone_account_shows_by_its_memberships_and_nothing_is_not_found(client, superadmin):
    superadmin("ann@example.com")
    gone = client.get("/superadmin/support/users/uid-gone").json()

    assert (gone["email"], gone["created_at"], gone["top_ups"]) == (None, None, [])
    assert gone["companies"] == [{"id": str(ACME.id), "name": "Acme", "role": "owner"}]
    assert client.get("/superadmin/support/users/nobody").status_code == 404


def test_a_superadmin_sees_a_candidates_metadata_never_their_answers(client, superadmin, caplog):
    superadmin("ann@example.com")

    with caplog.at_level(logging.INFO):
        response = client.get(f"/superadmin/support/candidates/{CID.id}")

    assert response.json() == {
        "invite_id": str(CID.id),
        "email": "cid@example.com",
        "name": "Cid",
        "status": "finished",
        "company_id": str(ACME.id),
        "company_name": "Acme",
        "interview_id": str(INTERVIEW.id),
        "interview_title": "Backend",
        "invited_at": "2026-10-01T00:00:00Z",
        "last_sent_at": "2026-10-01T00:00:00Z",
        "started_at": "2026-10-01T00:00:00Z",
        "finished_at": "2026-10-01T00:00:00Z",
        "grade": 80,
        "passed": True,
        "extra_time": 25,
        "signals": {"tab_leaves": 2, "copies": 1, "fast_answers": 3},
        "credits": "charged",
    }
    assert f"candidate {CID.id} of company {ACME.id} viewed by superadmin" in caplog.text
    assert "cid@example.com" not in caplog.text
    assert client.get(f"/superadmin/support/candidates/{uuid.uuid4()}").status_code == 404


def test_a_candidates_credits_say_held_while_set_aside(client, superadmin, monkeypatch):
    async def candidate_hold(key):
        return "open"

    monkeypatch.setattr(billing, "candidate_hold", candidate_hold)
    superadmin("ann@example.com")

    assert client.get(f"/superadmin/support/candidates/{CID.id}").json()["credits"] == "held"


def test_a_superadmin_sees_an_interview_with_its_topics_by_name(client, superadmin, caplog):
    superadmin("ann@example.com")

    with caplog.at_level(logging.INFO):
        response = client.get(f"/superadmin/support/interviews/{INTERVIEW.id}")

    assert response.json() == {
        "id": str(INTERVIEW.id),
        "title": "Backend",
        "status": "in_process",
        "company_id": str(ACME.id),
        "company_name": "Acme",
        "created_at": "2026-10-01T00:00:00Z",
        "generation_id": str(INTERVIEW.generation_id),
        "generation_failed": False,
        "topics": ["Python", "SQL"],
        "question_seconds": 60,
        "pass_mark": 70,
        "candidate_count": 1,
    }
    assert f"details of interview {INTERVIEW.id} of company {ACME.id} viewed" in caplog.text
    assert client.get(f"/superadmin/support/interviews/{uuid.uuid4()}").status_code == 404


def test_an_interviews_candidates_newest_first(client, superadmin):
    superadmin("ann@example.com")
    response = client.get(f"/superadmin/support/interviews/{INTERVIEW.id}/candidates")

    assert response.json() == [
        {
            "invite_id": str(CID.id),
            "email": "cid@example.com",
            "name": "Cid",
            "status": "finished",
            "grade": 80,
            "created_at": "2026-10-01T00:00:00Z",
        }
    ]
    missing = client.get(f"/superadmin/support/interviews/{uuid.uuid4()}/candidates")

    assert missing.status_code == 404
