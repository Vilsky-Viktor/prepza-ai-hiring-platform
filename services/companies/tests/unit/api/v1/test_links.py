import re
import uuid
from types import SimpleNamespace

import pytest
from fake_redis import FakeRedis
from fastapi import HTTPException
from prepza_common.auth.auth import current_user, optional_user
from prepza_common.auth.user import User

from companies.constants.invites import EMAIL_NOT_VERIFIED, NO_PLEDGE, InviteStatus
from companies.integrations import billing
from companies.main import app
from companies.models.interviews import Interview
from companies.repositories import companies, interviews, invites, link_invites
from companies.schemas.invites import InviteStartOut
from companies.services import invite_pages, link_start

# The limits' defaults: new candidates one link takes, and one address starts, an hour.
LINK_STARTS_PER_HOUR = 30
LINK_STARTS_PER_IP_HOUR = 10
TOO_MANY_REQUESTS = "Too many requests. Try again later."

INTERVIEW = Interview(
    id=uuid.uuid4(),
    company_id=uuid.uuid4(),
    generation_id=None,
    set_id=uuid.uuid4(),
    question_seconds=60,
    topic_limits={},
    link_token="abc",
)


@pytest.fixture
def linked(monkeypatch):
    """The link "abc" opens INTERVIEW; returns what was held and started, a way to set the
    candidate's current status or make billing refuse, and the rate counters and edited limits
    ("counts", "limits": Redis's)."""
    redis = FakeRedis()
    state = {
        "status": None,
        "broke": False,
        "held": [],
        "started": [],
        "counts": redis.counts,
        "limits": redis.limits,
    }

    async def get_by_link(session, token):
        return INTERVIEW if token == "abc" else None

    async def status_of(session, _interview_id, _email):
        return state["status"]

    async def held(session, _interview_id, _email):
        return state["status"], None

    async def hold(company_id, key):
        if state["broke"]:
            raise HTTPException(402, "Not enough credits. Top up to continue.")

        state["held"].append(key)

    async def for_link(session, interview_id, email, hold_key=None, details=None):
        return SimpleNamespace(email=email, hold_key=hold_key)

    async def start(invite, interview, user_id):
        state["started"].append(invite)

        return InviteStartOut(sessions=[])

    monkeypatch.setattr(interviews, "get_by_link", get_by_link)
    monkeypatch.setattr(invites, "held", held)
    monkeypatch.setattr(invites, "status_of", status_of)
    monkeypatch.setattr(link_invites, "for_link", for_link)
    monkeypatch.setattr(billing, "hold_candidate", hold)

    async def details(interview):
        return {"title": "Backend", "company": "Acme", "language": "en", "logo_path": None}

    async def no_flush():
        pass

    monkeypatch.setattr(link_start, "start_sessions", start)
    monkeypatch.setattr(link_start, "get_redis", lambda: redis)
    monkeypatch.setattr(link_start, "joined_details", details)
    monkeypatch.setattr(link_start.outbox_service, "flush_quietly", no_flush)
    app.dependency_overrides[current_user] = lambda: User(
        uid="cand", email="Cand@Example.com", email_verified=True
    )

    yield state

    app.dependency_overrides.clear()


def test_anyone_signed_in_starts_through_the_link_and_is_charged_like_an_invite(client, linked):
    assert client.post("/links/abc/start", json={"pledged": True}).status_code == 200
    # Set aside under the new invite's own key.
    (key,) = linked["held"]
    # A new key of its own, without the candidate's email.
    assert re.fullmatch(rf"{INTERVIEW.id}:[0-9a-f]{{32}}", key)
    assert [invite.email for invite in linked["started"]] == ["Cand@Example.com"]


def test_a_new_candidate_through_the_link_needs_the_pledge_and_uses_nothing_up(client, linked):
    response = client.post("/links/abc/start", json={"pledged": False})

    assert response.status_code == 422
    assert response.json()["detail"] == NO_PLEDGE
    assert linked["held"] == []
    assert linked["started"] == []
    assert linked["counts"] == {}


def test_a_candidate_back_through_the_link_continues_without_pledging_again(client, linked):
    linked["status"] = InviteStatus.IN_PROCESS

    assert client.post("/links/abc/start").status_code == 200
    assert len(linked["started"]) == 1


def test_a_new_invite_that_cant_be_saved_gives_its_credits_back(client, linked, monkeypatch):
    """Its interview was deleted meanwhile."""
    released = []

    async def gone(session, interview_id, email, hold_key=None, details=None):
        raise RuntimeError("interview deleted")

    async def release(key):
        released.append(key)

    monkeypatch.setattr(link_invites, "for_link", gone)
    monkeypatch.setattr(billing, "release_candidate", release)

    with pytest.raises(RuntimeError):
        client.post("/links/abc/start", json={"pledged": True})

    assert released == linked["held"] and len(released) == 1


def test_coming_back_continues_without_charging_again(client, linked):
    linked["status"] = "in_process"

    client.post("/links/abc/start", json={"pledged": True})

    assert linked["held"] == []
    assert len(linked["started"]) == 1


def test_one_attempt_each_and_a_closed_or_broke_link_says_so(client, linked):
    linked["status"] = "finished"
    assert client.post("/links/abc/start", json={"pledged": True}).status_code == 409

    linked["status"], linked["broke"] = None, True
    refused = client.post("/links/abc/start", json={"pledged": True})
    assert refused.status_code == 409
    assert refused.json()["detail"] == "This interview isn't taking new candidates right now."

    assert client.post("/links/nope/start", json={"pledged": True}).status_code == 404
    assert linked["started"] == []


def test_an_unverified_email_cant_start(client, linked):
    app.dependency_overrides[current_user] = lambda: User(
        uid="x", email="x@example.com", email_verified=False
    )

    response = client.post("/links/abc/start", json={"pledged": True})

    assert response.status_code == 403
    assert response.json()["detail"] == EMAIL_NOT_VERIFIED
    assert linked["held"] == []


def test_the_link_says_when_the_signed_in_person_already_finished(client, linked, monkeypatch):
    async def no_company(session, _company_id):
        return None

    async def title(_interview):
        return "Backend"

    async def found_set(_set_id):
        return {"topics": [{"id": str(uuid.uuid4()), "title": "Python", "question_count": 3}]}

    monkeypatch.setattr(companies, "get", no_company)
    monkeypatch.setattr(invite_pages, "interview_title", title)
    monkeypatch.setattr(invite_pages.set_cache, "get_set", found_set)
    linked["status"] = "finished"
    app.dependency_overrides[optional_user] = lambda: User(
        uid="cand", email="cand@example.com", email_verified=True
    )

    signed_in = client.get("/links/abc").json()
    app.dependency_overrides[optional_user] = lambda: None
    signed_out = client.get("/links/abc").json()

    assert signed_in["status"] == "finished"
    assert signed_out["status"] is None
    # The set's 3 questions at 60 seconds each.
    assert signed_out["total_minutes"] == 3


def test_a_link_takes_a_limited_number_of_new_candidates_an_hour(client, linked, limit_hits):
    linked["counts"][f"rate:link-starts:{INTERVIEW.id}"] = LINK_STARTS_PER_HOUR
    refused = client.post("/links/abc/start", json={"pledged": True})

    assert refused.status_code == 429
    assert refused.json() == {"detail": TOO_MANY_REQUESTS, "code": "rate_limited"}
    assert linked["held"] == []
    assert [(hit["limit"], hit["company_id"], hit["user_id"]) for hit in limit_hits] == [
        ("LINK_STARTS_PER_HOUR", str(INTERVIEW.company_id), "cand")
    ]


def test_a_links_hourly_limit_is_as_edited(client, linked):
    linked["limits"]["LINK_STARTS_PER_HOUR"] = "2"
    starts = [client.post("/links/abc/start", json={"pledged": True}).status_code for _ in range(3)]

    assert starts == [200, 200, 429]
    assert len(linked["held"]) == 2


def test_one_address_starts_a_limited_number_of_new_candidates_an_hour(client, linked):
    for _ in range(LINK_STARTS_PER_IP_HOUR):
        assert client.post("/links/abc/start", json={"pledged": True}).status_code == 200

    refused = client.post("/links/abc/start", json={"pledged": True})

    assert refused.status_code == 429
    assert refused.json() == {"detail": TOO_MANY_REQUESTS, "code": "rate_limited"}
    assert len(linked["held"]) == LINK_STARTS_PER_IP_HOUR


def test_one_addresss_hourly_limit_is_as_edited(client, linked, limit_hits):
    linked["limits"]["LINK_STARTS_PER_IP_HOUR"] = "1"
    starts = [client.post("/links/abc/start", json={"pledged": True}).status_code for _ in range(2)]

    assert starts == [200, 429]
    assert [hit["limit"] for hit in limit_hits] == ["LINK_STARTS_PER_IP_HOUR"]


def test_an_address_over_its_limit_uses_up_nothing_of_the_links(client, linked):
    linked["limits"]["LINK_STARTS_PER_IP_HOUR"] = "1"
    starts = [client.post("/links/abc/start", json={"pledged": True}).status_code for _ in range(5)]

    assert starts == [200] + [429] * 4
    # Only the one start that went through counts toward the link.
    assert linked["counts"][f"rate:link-starts:{INTERVIEW.id}"] == 1


def test_a_candidate_already_invited_is_never_held_back_by_the_limits(client, linked):
    linked["status"] = InviteStatus.IN_PROCESS
    linked["counts"][f"rate:link-starts:{INTERVIEW.id}"] = LINK_STARTS_PER_HOUR

    assert client.post("/links/abc/start", json={"pledged": True}).status_code == 200
    assert linked["counts"] == {f"rate:link-starts:{INTERVIEW.id}": LINK_STARTS_PER_HOUR}


def test_an_unverified_email_learns_nothing_of_that_addresss_status(client, linked, monkeypatch):
    async def no_company(session, _company_id):
        return None

    async def title(_interview):
        return "Backend"

    async def found_set(_set_id):
        return {"topics": []}

    monkeypatch.setattr(companies, "get", no_company)
    monkeypatch.setattr(invite_pages, "interview_title", title)
    monkeypatch.setattr(invite_pages.set_cache, "get_set", found_set)
    linked["status"] = "finished"
    app.dependency_overrides[optional_user] = lambda: User(
        uid="x", email="cand@example.com", email_verified=False
    )

    assert client.get("/links/abc").json()["status"] is None
