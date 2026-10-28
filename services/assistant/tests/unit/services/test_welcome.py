import asyncio
import uuid

import httpx
import pytest
from fastapi import HTTPException

from assistant.constants.welcome import Stage
from assistant.helpers.welcome import stage
from assistant.services import welcome

COMPANY = {"id": "c1", "interview_count": 0, "verified_domain": None}


@pytest.mark.parametrize(
    "companies, has_candidates, expected",
    [
        ([], False, Stage.NO_COMPANY),
        ([COMPANY], False, Stage.UNVERIFIED),
        ([{**COMPANY, "verified_domain": "acme.com"}], False, Stage.NO_INTERVIEWS),
        ([COMPANY, {**COMPANY, "interview_count": 2}], False, Stage.NO_CANDIDATES),
        ([{**COMPANY, "interview_count": 2}], True, Stage.HAS_CANDIDATES),
    ],
)
def test_the_furthest_stage_any_company_reached(companies, has_candidates, expected):
    assert stage(companies, has_candidates) == expected


def answering(monkeypatch, answers: dict):
    """companies answering each path with its JSON; the paths asked, in order."""
    asked = []

    async def get(service, path, query, token, language, via=None):
        asked.append(path)
        request = httpx.Request("GET", f"http://companies{path}")

        if path not in answers:
            return httpx.Response(502, request=request)

        return httpx.Response(200, json=answers[path], request=request)

    monkeypatch.setattr(welcome.services, "get", get)

    return asked


def test_candidates_are_looked_for_only_in_companies_with_interviews(monkeypatch):
    asked = answering(
        monkeypatch,
        {
            "/companies": [COMPANY, {**COMPANY, "id": "c2", "interview_count": 1}],
            "/interviews": [{"candidate_count": 3}],
        },
    )

    assert asyncio.run(welcome.welcome_stage(None, "token", "en")) == Stage.HAS_CANDIDATES
    assert asked == ["/companies", "/interviews"]


def test_the_page_company_alone_decides(monkeypatch):
    company_id = uuid.uuid4()
    one = {**COMPANY, "interview_count": 1}
    answering(
        monkeypatch, {f"/companies/{company_id}": one, "/interviews": [{"candidate_count": 0}]}
    )

    assert asyncio.run(welcome.welcome_stage(company_id, "token", "en")) == Stage.NO_CANDIDATES


def test_companies_failing_is_a_503(monkeypatch):
    answering(monkeypatch, {})

    with pytest.raises(HTTPException) as error:
        asyncio.run(welcome.welcome_stage(None, "token", "en"))

    assert error.value.status_code == 503
