import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from prepza_common.config.constants import MAX_PAGE_SIZE

from companies.constants.audit import VIA_API
from companies.constants.invites import EXTRA_TIME_STARTED, NO_EMAILS_FOR_GUEST
from companies.repositories import candidates, companies, interviews, invites
from companies.services import candidate_changes, candidate_invites, candidate_results, credits
from companies.services import outbox as outbox_service
from tests.unit.api.v1.test_internal_api import COMPANY_ID, HEADERS, INTERVIEW, OTHER_ID

BASE = f"/internal/companies/{COMPANY_ID}"


@pytest.fixture
def world(monkeypatch):
    """The company's interview with one candidate (`state["invite"]`); returns what was done."""
    state = {
        "invite": SimpleNamespace(
            id=uuid.uuid4(), email="anna@example.com", status="invited", guest=False
        ),
        "done": [],
    }

    async def get_interview(session, interview_id):
        return INTERVIEW if interview_id == INTERVIEW.id else None

    async def get_candidate(session, interview_id, invite_id):
        invite = state["invite"]

        return invite if invite_id == invite.id else None

    async def get_company(session, company_id):
        return SimpleNamespace(id=company_id) if company_id == COMPANY_ID else None

    def record(name):
        async def done(*args, **kwargs):
            state["done"].append((name, *args))

        return done

    async def outbox():
        pass

    monkeypatch.setattr(interviews, "get", get_interview)
    monkeypatch.setattr(candidates, "get", get_candidate)
    monkeypatch.setattr(companies, "get", get_company)
    monkeypatch.setattr(candidate_changes, "remove", record("remove"))
    monkeypatch.setattr(candidate_invites, "invite", record("invite"))
    monkeypatch.setattr(outbox_service, "flush_quietly", outbox)

    return state


def candidate_path(state, company_id=COMPANY_ID):
    return f"/internal/companies/{company_id}/interviews/{INTERVIEW.id}/candidates/{state['invite'].id}"


def test_a_candidate_is_removed_as_the_keys_creator_through_the_api(client, world):
    response = client.delete(candidate_path(world), params={"user_id": "ann"}, headers=HEADERS)
    other = client.delete(
        candidate_path(world, OTHER_ID), params={"user_id": "ann"}, headers=HEADERS
    )

    assert (response.status_code, other.status_code) == (204, 404)
    assert world["done"] == [("remove", INTERVIEW, world["invite"], "ann", VIA_API)]


@pytest.fixture
def written(monkeypatch, world):
    """The changes written to the candidate, as the database would take them."""
    changes = []

    async def change(session, invite_id, values, statuses):
        if world["invite"].status not in statuses:
            return False

        changes.append(values)

        return True

    monkeypatch.setattr(invites, "change", change)

    return changes


def test_a_candidates_name_and_extra_time_change_together(client, world, written, audited):
    body = {"name": "  Anna Lee ", "extra_time": 25}
    response = client.patch(
        candidate_path(world), params={"user_id": "ann"}, json=body, headers=HEADERS
    )
    blank = client.patch(
        candidate_path(world), params={"user_id": "ann"}, json={"name": " "}, headers=HEADERS
    )

    assert (response.status_code, blank.status_code) == (204, 204)
    assert written == [{"name": "Anna Lee", "extra_time": 25}, {"name": None}]
    assert [event[2] for event in audited] == [
        "candidate_renamed",
        "extra_time_set",
        "candidate_renamed",
    ]


@pytest.mark.parametrize(
    ("status", "code", "detail"),
    [("in_process", 409, EXTRA_TIME_STARTED), ("deleted", 404, "Candidate not found")],
)
def test_a_refused_change_leaves_the_name_as_it_was(
    client, world, written, audited, status, code, detail
):
    """One refused field refuses the whole change: the name isn't written either."""
    world["invite"].status = status
    body = {"name": "Anna Lee", "extra_time": 25}
    response = client.patch(
        candidate_path(world), params={"user_id": "ann"}, json=body, headers=HEADERS
    )

    assert (response.status_code, response.json()["detail"]) == (code, detail)
    # The public API passes the reason on with a code its clients branch on.
    assert response.json().get("code") == ("candidate_started" if code == 409 else None)
    assert written == [] and audited == []


def test_a_candidate_who_started_meanwhile_keeps_their_time_and_name(
    client, world, written, monkeypatch
):
    """Read before they started, written after: the guarded write refuses it."""
    invite = world["invite"]

    async def get_candidate(session, interview_id, invite_id):
        return SimpleNamespace(**{**vars(invite), "status": "invited"})

    monkeypatch.setattr(candidates, "get", get_candidate)
    invite.status = "in_process"
    body = {"name": "Anna Lee", "extra_time": 25}
    response = client.patch(
        candidate_path(world), params={"user_id": "ann"}, json=body, headers=HEADERS
    )

    assert (response.status_code, response.json()["detail"]) == (409, EXTRA_TIME_STARTED)
    assert written == []


def test_a_reminder_goes_out_again_but_not_to_a_guest(client, world):
    sent = client.post(
        f"{candidate_path(world)}/resend", params={"user_id": "ann"}, headers=HEADERS
    )
    world["invite"].guest = True
    guest = client.post(
        f"{candidate_path(world)}/resend", params={"user_id": "ann"}, headers=HEADERS
    )

    assert sent.status_code == 204
    assert guest.status_code == 409
    assert guest.json() == {"detail": NO_EMAILS_FOR_GUEST, "code": "invited_without_sign_in"}
    [(name, interview, _company, sender, email)] = world["done"]
    assert (name, interview, sender.uid, email) == ("invite", INTERVIEW, "ann", "anna@example.com")


def test_a_candidate_is_found_by_exact_email_in_full_and_credits_are_read(
    client, world, monkeypatch
):
    asked = []
    invite = SimpleNamespace(
        **vars(world["invite"]),
        name="Anna Lee",
        token="tok-1",
        flagged=False,
        extra_time=0,
        grade=None,
        created_at=datetime.now(UTC),
        updated_at=None,
        started_at=None,
        finished_at=None,
    )

    async def company_page(session, company_id, offset, limit, q="", email=""):
        asked.append((email, limit))

        return [(invite, SimpleNamespace(**vars(INTERVIEW), title="Backend"))]

    async def invite_scores(invite_ids):
        asked.append(("scores", invite_ids))

        return {str(invite.id): {"progress": 40}}

    async def credits_of(company_id):
        return {"available": 1500, "low": False}

    monkeypatch.setattr(candidates, "company_page", company_page)
    monkeypatch.setattr(candidate_results.rounds, "invite_scores", invite_scores)
    monkeypatch.setattr(credits, "credits_of", credits_of)

    found = client.post(
        f"{BASE}/candidates/search", json={"email": "anna@example.com"}, headers=HEADERS
    )
    balance = client.get(f"{BASE}/credits", headers=HEADERS)

    [row] = found.json()
    assert (row["id"], row["interview_id"]) == (str(invite.id), str(INTERVIEW.id))
    assert (row["name"], row["progress"], row["invite_token"]) == ("Anna Lee", 40, "tok-1")
    # One page of matches, their results asked of rounds at once.
    assert asked == [("anna@example.com", MAX_PAGE_SIZE), ("scores", [invite.id])]
    assert balance.json()["available"] == 1500


def test_the_api_routes_need_a_service_token(client, world):
    assert client.get(f"{BASE}/credits").status_code in (401, 403)
