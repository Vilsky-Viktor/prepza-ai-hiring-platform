import asyncio

# The key fixture is imported from test_public_routes and named in the tests.
# ruff: noqa: F811
import pytest
from fastapi import HTTPException

from app.constants.api import IDEMPOTENCY_KEY_REUSED
from app.integrations import companies
from app.services import idempotency
from tests.unit.conftest import CANDIDATE, COMPANY, INTERVIEW, interview
from tests.unit.test_public_routes import KEY, call, key  # noqa: F401 (fixture)

CANDIDATE_PATH = f"/interviews/{INTERVIEW}/candidates/{CANDIDATE}"


def post(client, path, body, idempotency_key=None):
    headers = {"Authorization": f"Bearer {KEY}"}

    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key

    return client.post(path, json=body, headers=headers)


class FakeRedis:
    def __init__(self):
        self.values = {}

    async def set(self, name, value, nx=False, ex=None):
        if nx and name in self.values:
            return None

        self.values[name] = value.encode() if isinstance(value, str) else value

        return True

    async def get(self, name):
        return self.values.get(name)

    async def delete(self, name):
        self.values.pop(name, None)


@pytest.fixture
def changes(monkeypatch, companies_api):
    """The companies service's writes, recorded."""
    done = []

    def record(name):
        async def change(*args):
            done.append((name, *args))

        return change

    for name in ("remove_candidate", "change_candidate", "resend"):
        monkeypatch.setattr(companies, name, record(name))

    async def create_interview(company_id, text, language, user_id):
        done.append(("create_interview", company_id, text, language, user_id))

        return {"id": str(INTERVIEW)}

    monkeypatch.setattr(companies, "create_interview", create_interview)
    monkeypatch.setattr(idempotency, "get_redis", lambda: redis)
    redis = FakeRedis()

    return done


def test_a_key_makes_an_interview_as_its_creator_once_per_idempotency_key(
    client,
    key,
    changes,
):
    body = {"job_description": "Backend developer", "language": "de"}
    first = post(client, "/interviews", body, "abc")
    again = post(client, "/interviews", body, "abc")

    assert first.status_code == again.status_code == 201
    assert first.json()["id"] == str(INTERVIEW)
    assert changes == [("create_interview", COMPANY, "Backend developer", "de", "u1")]


def test_an_invite_retried_with_its_idempotency_key_goes_out_once(
    client,
    companies_api,
    key,
    changes,
):
    body = {"email": "bob@example.com"}
    for _ in range(2):
        response = post(client, f"/interviews/{INTERVIEW}/candidates", body, "invite-1")
        assert response.status_code == 201

    assert companies_api["sent"] == [(INTERVIEW, "bob@example.com", "u1")]


def test_a_retried_interview_without_a_key_is_made_once_and_another_one_again(client, key, changes):
    """No key from the client: the same request from the same API key within the retry window
    returns the first interview; another body makes another."""
    body = {"job_description": "Backend developer", "language": "de"}
    first = post(client, "/interviews", body)
    again = post(client, "/interviews", body)
    other = post(client, "/interviews", {**body, "job_description": "Data engineer"})

    assert first.status_code == again.status_code == other.status_code == 201
    assert [change[2] for change in changes] == ["Backend developer", "Data engineer"]


def test_a_retried_invite_without_a_key_returns_the_candidate_as_they_are(
    client, companies_api, key, changes
):
    body = {"email": "bob@example.com"}
    first = post(client, f"/interviews/{INTERVIEW}/candidates", body)
    again = post(client, f"/interviews/{INTERVIEW}/candidates", body)

    assert (first.status_code, again.status_code) == (201, 200)
    assert first.json()["id"] == again.json()["id"]
    assert companies_api["sent"] == [(INTERVIEW, "bob@example.com", "u1")]


def test_a_key_used_again_for_another_request_is_refused(client, companies_api, key, changes):
    path = f"/interviews/{INTERVIEW}/candidates"
    post(client, path, {"email": "bob@example.com"}, "invite-3")
    reused = post(client, path, {"email": "eve@example.com"}, "invite-3")

    assert reused.status_code == 422
    assert reused.json()["detail"] == IDEMPOTENCY_KEY_REUSED
    assert companies_api["sent"] == [(INTERVIEW, "bob@example.com", "u1")]


def test_a_failed_request_frees_its_idempotency_key(client, companies_api, key, changes):
    body = {"email": "bob@example.com"}
    path = f"/interviews/{INTERVIEW}/candidates"
    companies_api["refuse"] = 402
    refused = post(client, path, body, "invite-2")
    companies_api["refuse"] = None
    sent = post(client, path, body, "invite-2")

    assert (refused.status_code, sent.status_code) == (402, 201)


def test_a_candidate_is_renamed_given_extra_time_resent_and_removed(client, key, changes):
    renamed = call(client, "PATCH", CANDIDATE_PATH, json={"name": "Anna", "extra_time": 25})
    unchanged = call(client, "PATCH", CANDIDATE_PATH, json={})
    unnamed = call(client, "PATCH", CANDIDATE_PATH, json={"name": None})
    resent = call(client, "POST", f"{CANDIDATE_PATH}/resend")
    removed = call(client, "DELETE", CANDIDATE_PATH)
    wrong_time = call(client, "PATCH", CANDIDATE_PATH, json={"extra_time": 30})

    assert renamed.status_code == unchanged.status_code == unnamed.status_code == 200
    assert (resent.status_code, removed.status_code, wrong_time.status_code) == (204, 204, 422)
    assert changes == [
        # Both changes in one call, so companies makes them together or not at all.
        (
            "change_candidate",
            COMPANY,
            INTERVIEW,
            CANDIDATE,
            {"name": "Anna", "extra_time": 25},
            "u1",
        ),
        ("change_candidate", COMPANY, INTERVIEW, CANDIDATE, {"name": ""}, "u1"),
        ("resend", COMPANY, INTERVIEW, CANDIDATE, "u1"),
        ("remove_candidate", COMPANY, INTERVIEW, CANDIDATE, "u1"),
    ]


def test_companies_refusals_reach_the_client(client, key, changes, monkeypatch):
    async def started(*args):
        raise HTTPException(409, "The candidate already started.")

    monkeypatch.setattr(companies, "change_candidate", started)

    response = call(client, "PATCH", CANDIDATE_PATH, json={"extra_time": 50})

    assert response.status_code == 409


def test_a_candidate_is_found_by_email_across_interviews_and_credits_are_read(
    client,
    key,
    companies_api,
    monkeypatch,
):
    async def find(company_id, email):
        return [{"interview_id": str(INTERVIEW), "candidate_id": str(CANDIDATE)}]

    async def credits(company_id):
        return {"available": 1500, "reserved": 500, "candidates": 3, "low": False, "x": 1}

    monkeypatch.setattr(companies, "find_candidates", find)
    monkeypatch.setattr(companies, "credits", credits)

    found = call(client, "GET", "/candidates", params={"email": "bob@example.com"})
    bad = call(client, "GET", "/candidates", params={"email": "not-an-email"})
    balance = call(client, "GET", "/credits")

    assert [row["id"] for row in found.json()] == [str(CANDIDATE)]
    assert bad.status_code == 422
    assert balance.json() == {"available": 1500, "reserved": 500, "candidates": 3, "low": False}
    assert interview()["id"]


def test_lists_pass_on_what_changed_since_and_after_which_item(
    client, key, companies_api, monkeypatch
):
    asked = []

    async def interviews(company_id, offset, limit, since=None, after=None):
        asked.append((since.isoformat() if since else None, after))

        return []

    monkeypatch.setattr(companies, "interviews", interviews)
    params = {"updated_since": "2026-10-15T10:00:00Z", "after": str(INTERVIEW)}

    assert call(client, "GET", "/interviews", params=params).status_code == 200
    assert (
        call(client, "GET", "/interviews", params={"updated_since": "yesterday"}).status_code == 422
    )
    assert asked == [("2026-10-15T10:00:00+00:00", INTERVIEW)]


def test_a_result_kept_before_requests_were_fingerprinted_is_still_returned(monkeypatch):
    redis = FakeRedis()
    redis.values["old"] = str(INTERVIEW).encode()
    monkeypatch.setattr(idempotency, "get_redis", lambda: redis)

    async def run():
        raise AssertionError("ran again")

    assert asyncio.run(idempotency.once("old", 60, "any", run)) == str(INTERVIEW)


def test_a_retry_while_the_first_still_runs_is_refused(monkeypatch):
    redis = FakeRedis()
    redis.values["running"] = b"req:pending"
    monkeypatch.setattr(idempotency, "get_redis", lambda: redis)

    async def run():
        return "x"

    with pytest.raises(HTTPException) as refused:
        asyncio.run(idempotency.once("running", 60, "req", run))

    assert refused.value.status_code == 409
