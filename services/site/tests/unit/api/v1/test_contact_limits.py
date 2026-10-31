import pytest
from testee_common.ai.ai_constants import LIMIT_HIT
from testee_common.config.constants import RATE_LIMITED
from testee_common.limits.limit_list import LIMITS

import site_content.api.v1.help as help_routes

CONTACT = {"name": "Ann", "email": "ann@example.com", "message": "Do you offer invoices?"}


@pytest.fixture(autouse=True)
def nothing_sent(monkeypatch):
    """The contact form's messages go nowhere."""

    def keep_nothing(*args):
        return None

    async def nothing(*args):
        return None

    monkeypatch.setattr(help_routes.contact_service.outbox, "add", keep_nothing)
    monkeypatch.setattr(help_routes.contact_service.outbox_service, "flush_quietly", nothing)


def current(redis, name: str, edited: bool) -> int:
    """The limit's value: an edited one (in Redis, as the Controls tab saves it), or its
    default."""
    if not edited:
        return LIMITS[name].default

    value = LIMITS[name].lowest + 1
    redis.limits[name] = value

    return value


def hits(published) -> list[tuple]:
    return [(data["limit"], data["user_id"]) for kind, data in published if kind == LIMIT_HIT]


@pytest.mark.parametrize("edited", [False, True])
@pytest.mark.parametrize(
    ("name", "key"),
    [
        ("CONTACT_IP_LIMIT", "rate:contact:ip:testclient"),
        ("CONTACT_DAILY_LIMIT", "rate:contact:all"),
    ],
)
def test_each_contact_limit_refuses_past_its_current_value(
    client, redis, published, name, key, edited
):
    value = current(redis, name, edited)
    redis.counts[key] = value - 1

    last = client.post("/help/contact", json=CONTACT)
    refused = client.post("/help/contact", json=CONTACT)

    assert last.status_code == 204
    assert refused.status_code == 429
    assert refused.json()["detail"] == RATE_LIMITED
    assert hits(published) == [(name, None)]
