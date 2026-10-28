import pytest
from prepza_common.auth.service_auth import issue_token
from prepza_common.limits.limit_list import LIMITS
from prepza_common.redis import memory_cache

from tests.unit.api.v1.test_help import CATALOG, fake_catalog

# Limits as the Controls tab edited them; none is its default.
EDITED = {
    "MAX_OWNED_COMPANIES": 7,
    "INTERVIEWS_PER_DAY": 25,
    "INTERVIEWS_PER_DAY_UNPAID": 4,
    "MAX_INTERVIEWS_WITHOUT_CANDIDATES": 9,
    "MAX_INTERVIEWS_WITHOUT_CANDIDATES_UNPAID": 2,
    "QUESTION_SECONDS_BASIC": 50,
    "QUESTION_SECONDS_MEDIUM": 65,
    "QUESTION_SECONDS_HARD": 90,
}


def named(text: str, limits: dict) -> list[str]:
    """Where the guide names each limit, with the value it names."""
    places = [
        f"can own up to {limits['MAX_OWNED_COMPANIES']})",
        f"up to {limits['INTERVIEWS_PER_DAY_UNPAID']} a day per company",
        f"({limits['INTERVIEWS_PER_DAY']} after)",
        f"at most {limits['MAX_INTERVIEWS_WITHOUT_CANDIDATES_UNPAID']} generated",
        f"({limits['MAX_INTERVIEWS_WITHOUT_CANDIDATES']} after the first top-up)",
        f"{limits['QUESTION_SECONDS_BASIC']} seconds for a basic test",
        f"{limits['QUESTION_SECONDS_MEDIUM']} for a medium one",
        f"{limits['QUESTION_SECONDS_HARD']} for a hard one",
    ]

    return [place for place in places if place in text]


@pytest.fixture(autouse=True)
def prices(monkeypatch):
    monkeypatch.setattr("site_content.services.help.billing.catalog", fake_catalog(CATALOG))


def test_the_platform_guide_names_the_limits_current_values(client, redis, monkeypatch):
    defaults = {name: LIMITS[name].default for name in EDITED}

    before = client.get("/help/guide").text
    redis.limits.update(EDITED)
    # Once the kept limits and guide expire, both are read again.
    monkeypatch.setattr(memory_cache, "_entries", {})
    after = client.get("/help/guide").text

    assert len(named(before, defaults)) == len(EDITED)
    assert len(named(after, EDITED)) == len(EDITED)
    assert named(after, defaults) == []


def test_the_help_chats_knowledge_names_the_limits_current_values(client, redis):
    redis.limits.update(EDITED)
    token = issue_token("assistant", "site", "test-secret-that-is-at-least-32-bytes")

    found = client.get("/internal/help/knowledge", headers={"Authorization": f"Bearer {token}"})

    assert len(named(found.json()["knowledge"], EDITED)) == len(EDITED)
