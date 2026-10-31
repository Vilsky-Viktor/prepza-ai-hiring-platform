"""Who a public API call gets through as: no key or an unknown or expired one is refused; a key
belongs to its company and works whoever made it; a company's keys share one rate limit (open
while Redis is down); the key's use is noted at most once a minute."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError
from testee_common.auth.tokens import hashed
from testee_common.limits import rate_limit

from api.constants.api import LAST_USED_EVERY
from api.constants.permissions import Permission
from api.integrations import companies
from tests.unit.api_keys import call
from tests.unit.conftest import COMPANY


@pytest.mark.parametrize("sent", [None, "te_wrong", "not-even-a-key"])
def test_no_key_or_an_unknown_one_is_refused(client, companies_api, stored, sent):
    response = call(client, "GET", "/interviews", key=sent)

    assert response.status_code == 401
    assert stored["used"] == []


def test_an_expired_key_is_refused(client, companies_api, key):
    key.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    response = call(client, "GET", "/interviews")

    assert response.status_code == 401
    assert response.json()["detail"] == "This API key has expired"


@pytest.mark.parametrize("role", ["viewer", None])
def test_a_key_works_whoever_made_it_and_never_asks_about_them(
    client, companies_api, key, role, monkeypatch
):
    """Its maker now a viewer, gone from the company, or with their account deleted."""
    companies_api["roles"]["u1"] = role
    key.created_by = None if role is None else "u1"
    asked = []

    async def access(company_id, user_id):
        asked.append(user_id)

    monkeypatch.setattr(companies, "access", access)

    assert call(client, "GET", "/interviews").status_code == 200
    assert asked == []


def test_over_the_rate_limit_is_refused(client, companies_api, key, stored):
    stored["limited"] = True

    assert call(client, "GET", "/interviews").status_code == 429


def test_a_companys_keys_share_one_rate_limit(client, companies_api, key, stored):
    other = type("Key", (), {})()
    other.id, other.company_id, other.created_by = uuid.uuid4(), COMPANY, "u1"
    other.hash, other.expires_at, other.last_used_at = hashed("te_other"), None, None
    other.permissions, other.allowed_ips = list(Permission), []
    stored["keys"].append(other)
    call(client, "GET", "/interviews")
    call(client, "GET", "/interviews", key="te_other")

    assert stored["counted"] == [f"rate:api:{COMPANY}"] * 2


def test_a_refused_key_isnt_counted(client, companies_api, key, stored):
    key.expires_at = datetime.now(UTC) - timedelta(minutes=1)

    assert call(client, "GET", "/interviews").status_code == 401
    assert stored["counted"] == []


def test_with_redis_down_requests_go_through_unlimited(client, companies_api, key, monkeypatch):
    async def down(*args, **kwargs):
        raise RedisConnectionError("down")

    monkeypatch.setattr(rate_limit, "hit", down)

    assert call(client, "GET", "/interviews").status_code == 200


def test_a_key_used_within_the_minute_isnt_noted_again(client, companies_api, key, stored):
    key.last_used_at = datetime.now(UTC) - timedelta(seconds=10)
    call(client, "GET", "/interviews")
    key.last_used_at = datetime.now(UTC) - LAST_USED_EVERY
    call(client, "GET", "/interviews")

    assert stored["used"] == [key.id]
