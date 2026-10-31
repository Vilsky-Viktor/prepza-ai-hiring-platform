import pytest
from fake_redis import FakeRedis
from testee_common.auth.auth import current_user
from testee_common.auth.user import User

from companies.api.v1 import bulk_invites
from companies.api.v1 import limits as limits_route
from companies.main import app
from companies.repositories import audit
from companies.services import candidate_invites
from tests.unit.api.v1.test_candidate_invites import COMPANY_ID, INTERVIEW_ID, URL, invite_setup

TOO_MANY_REQUESTS = "Too many requests. Try again later."


@pytest.fixture
def invites_redis(monkeypatch):
    """Bob invites to Acme's interview (test_candidate_invites), with the limits and counters in
    the Redis returned; the action log isn't what these tests check."""
    redis = FakeRedis()

    async def nothing(session, *args, **kwargs):
        return None

    invite_setup(monkeypatch)
    monkeypatch.setattr(candidate_invites, "get_redis", lambda: redis)
    monkeypatch.setattr(bulk_invites, "get_redis", lambda: redis)
    monkeypatch.setattr(audit, "record", nothing)
    yield redis
    app.dependency_overrides.clear()


def emails(count):
    return " ".join(f"c{number}@example.com" for number in range(count))


@pytest.mark.parametrize(("edited", "most"), [(None, 100), (2, 2)])
def test_a_list_holds_at_most_the_bulk_limits_emails(
    client, invites_redis, limit_hits, edited, most
):
    if edited:
        invites_redis.limits["MAX_BULK_INVITES"] = str(edited)

    refused = client.post(f"{URL}/bulk", json={"text": emails(most + 1)})
    allowed = client.post(f"{URL}/bulk", json={"text": emails(most)})

    assert refused.status_code == 422
    assert refused.json() == {"detail": f"Too many emails in one list: the most is {most}."}
    assert allowed.status_code == 200
    assert len(allowed.json()["invited"]) == most
    assert [(hit["limit"], hit["company_id"], hit["user_id"]) for hit in limit_hits] == [
        ("MAX_BULK_INVITES", str(COMPANY_ID), "bob")
    ]


# Each email limit, the counter it's under, and its default.
EMAIL_LIMITS = [
    ("EMAIL_HOURLY_LIMIT", "rate:emails:hour:bob", 100),
    ("EMAIL_DAILY_LIMIT", "rate:emails:day:bob", 200),
    ("EMAIL_RECIPIENT_DAILY_LIMIT", f"rate:emails:recipient:{INTERVIEW_ID}:carol@example.com", 3),
]


@pytest.mark.parametrize(("name", "key", "default"), EMAIL_LIMITS)
def test_invite_emails_are_refused_over_each_email_limits_default(
    client, invites_redis, limit_hits, name, key, default
):
    invites_redis.counts[key] = default - 1
    allowed = client.post(URL, json={"email": "carol@example.com"})
    refused = client.post(URL, json={"email": "carol@example.com"})

    assert allowed.status_code == 201
    assert refused.status_code == 429
    assert refused.json() == {"detail": TOO_MANY_REQUESTS, "code": "rate_limited"}
    assert [(hit["limit"], hit["company_id"], hit["user_id"]) for hit in limit_hits] == [
        (name, str(COMPANY_ID), "bob")
    ]


@pytest.mark.parametrize(("name", "key", "default"), EMAIL_LIMITS)
def test_invite_emails_are_refused_over_each_email_limit_as_edited(
    client, invites_redis, limit_hits, name, key, default
):
    invites_redis.limits[name] = "2"
    codes = [client.post(URL, json={"email": "carol@example.com"}).status_code for _ in range(3)]

    assert codes == [201, 200, 429]
    assert [hit["limit"] for hit in limit_hits] == [name]


@pytest.mark.parametrize(("edited", "most"), [(None, 100), (40, 40)])
def test_the_invite_hints_read_the_bulk_limits_current_value(client, monkeypatch, edited, most):
    redis = FakeRedis({"MAX_BULK_INVITES": edited} if edited else None)
    monkeypatch.setattr(limits_route, "get_redis", lambda: redis)
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True
    )
    response = client.get("/limits")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"max_bulk_invites": most}


def test_the_limits_are_for_signed_in_users_only(client):
    assert client.get("/limits").status_code == 401
