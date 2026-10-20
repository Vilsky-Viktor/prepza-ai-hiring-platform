import asyncio

import pytest
from prepza_common import memory_cache
from prepza_common.auth import current_user
from prepza_common.limit_list import LIMITS
from prepza_common.user import User

from app.constants.help import HELP_ALL_KEY, HELP_SPEND_KEY
from app.main import app
from app.schemas.help import HelpMessage
from app.services.help import build_messages
from tests.unit.test_help import CATALOG, fake_catalog

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
    monkeypatch.setattr("app.services.help.billing.catalog", fake_catalog(CATALOG))


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


def test_the_help_chat_names_the_limits_current_values(redis):
    redis.limits.update(EDITED)
    question = [HelpMessage(role="user", content="How many companies can I own?")]

    system = asyncio.run(build_messages(question, "en", CATALOG))[0].content

    assert len(named(system, EDITED)) == len(EDITED)


@pytest.fixture
def signed_in(monkeypatch):
    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")

    def sign_in(email):
        app.dependency_overrides[current_user] = lambda: User(
            uid=email,
            email=email,
            email_verified=True,
            sign_in_provider="google.com",
        )

    yield sign_in
    app.dependency_overrides.clear()


def test_the_superadmin_sees_how_much_of_the_help_chats_budgets_is_used(client, redis, signed_in):
    redis.limits["HELP_TOKENS_PER_DAY"] = 2_000_000
    redis.counts[HELP_SPEND_KEY] = 500_000
    redis.counts[HELP_ALL_KEY] = 12
    signed_in("ann@example.com")

    response = client.get("/superadmin/budgets")

    assert response.status_code == 200
    assert [
        (item["name"], item["used"], item["limit"], item["unit"]) for item in response.json()
    ] == [
        ("HELP_TOKENS_PER_DAY", 500_000, 2_000_000, "tokens"),
        ("HELP_DAILY_LIMIT", 12, LIMITS["HELP_DAILY_LIMIT"].default, "calls"),
    ]


def test_nobody_else_sees_the_budgets(client, signed_in):
    signed_in("bob@example.com")

    assert client.get("/superadmin/budgets").status_code == 404
