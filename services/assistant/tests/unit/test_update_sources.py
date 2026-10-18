"""What get_updates reads: which companies, from which services, and credits for whom."""

import asyncio
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from prepza_common.i18n import translate

from app.constants.tool_calls import SERVICE_UNAVAILABLE
from app.integrations import billing, services
from app.integrations import update_sources as sources
from app.services.update_sources import Refused, read

UNTIL = datetime(2026, 10, 18, 9, tzinfo=UTC)
PERIOD = (UNTIL - timedelta(days=1), UNTIL)
OPEN = {"id": "open", "name": "Open", "ai_apps_allowed": True, "can_edit": True}
CLOSED = {"id": "closed", "name": "Closed", "ai_apps_allowed": False, "can_edit": True}
VIEWED = {"id": "viewed", "name": "Viewed", "ai_apps_allowed": True, "can_edit": False}


@pytest.fixture
def asked(monkeypatch):
    """The user's companies, and what each service was asked: one finished candidate per
    company it's asked about, and every company it's asked about low on credits."""
    made = {"low": []}

    async def get(service, path, query, token, language, via=None):
        request = httpx.Request("GET", f"http://{service}{path}")

        return httpx.Response(200, json=[OPEN, CLOSED, VIEWED], request=request)

    async def updates(service, path, company_ids, period):
        made[service] = (company_ids, period)

        if service != "companies":
            return []

        return [
            {
                "kind": "candidate_finished",
                "at": UNTIL.isoformat(),
                "company_id": company_id,
                "title": "Backend",
                "email": "ann@example.com",
                "link": f"/companies/{company_id}/candidates/1",
            }
            for company_id in company_ids
        ]

    async def low_companies(company_ids):
        made["low"].append(company_ids)

        return [{"company_id": company_id, "candidates": 0} for company_id in company_ids]

    monkeypatch.setattr(services, "get", get)
    monkeypatch.setattr(sources, "updates", updates)
    monkeypatch.setattr(billing, "low_companies", low_companies)

    return made


def reading(arguments=None, via="mcp", sees_credits=True) -> dict:
    return asyncio.run(
        read(arguments or {}, "token", "de", PERIOD, via, "https://site", sees_credits)
    )


def names(result: dict) -> list[str]:
    return [company["name"] for company in result["companies"]]


def test_an_ai_app_reads_only_companies_that_allow_ai_apps(asked):
    result = reading()

    for service in ("companies", "ats", "library", "notifications"):
        assert asked[service] == (["open", "viewed"], PERIOD)

    assert names(result) == ["Open", "Viewed"]


def test_prepzas_own_assistant_reads_every_company(asked):
    reading(via="assistant")

    assert asked["companies"][0] == ["open", "closed", "viewed"]


def test_low_credits_only_for_companies_the_user_owns_or_runs(asked):
    result = reading()

    assert asked["low"] == [["open"]]
    assert result["summary"]["credits_low"] == 1


def test_low_credits_never_without_the_permission_to_read_them(asked):
    result = reading(sees_credits=False)

    assert asked["low"] == []
    assert "credits_low" not in result["summary"]


def test_a_company_id_reads_only_that_company(asked):
    result = reading({"company_id": "viewed"})

    assert asked["companies"][0] == ["viewed"]
    assert asked["low"] == []
    assert names(result) == ["Viewed"]


def test_with_no_company_to_read_nothing_is_asked(asked):
    result = reading({"company_id": "closed"})

    assert "companies" not in asked
    assert result["companies"] == [] and result["summary"] == {}


def test_a_service_that_doesnt_answer_is_a_refusal_in_the_users_language(asked, monkeypatch):
    async def down(service, path, company_ids, period):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(sources, "updates", down)

    with pytest.raises(Refused) as refused:
        reading()

    assert (refused.value.status, refused.value.detail) == (
        503,
        translate(SERVICE_UNAVAILABLE, "de"),
    )
