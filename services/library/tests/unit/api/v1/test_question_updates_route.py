"""/internal/questions/updates: the questions of companies' interviews newly flagged or fixed,
for the assistant's get_updates tool only; any other service is refused."""

from datetime import UTC, datetime

import pytest
from prepza_common.auth.service_auth import issue_token
from prepza_common.config.constants import MAX_UPDATES
from prepza_common.http.http import bearer

from library.repositories import question_updates

SECRET = "test-secret-that-is-at-least-32-bytes"
SINCE = datetime(2026, 10, 1, tzinfo=UTC)
UNTIL = datetime(2026, 10, 2, tzinfo=UTC)
FLAGGED_AT = datetime(2026, 10, 1, 9, tzinfo=UTC)
FIXED_AT = datetime(2026, 10, 1, 12, tzinfo=UTC)
BODY = {
    "company_ids": ["company-a", "company-b"],
    "since": SINCE.isoformat(),
    "until": UNTIL.isoformat(),
}


@pytest.fixture
def between(monkeypatch):
    asked = []

    async def found(company_ids, since, until, limit):
        asked.append((company_ids, since, until, limit))

        return [
            ("question_flagged", FLAGGED_AT, "company-a", "Backend", "Python"),
            ("question_fixed", FIXED_AT, "company-b", "Frontend", "React"),
        ]

    async def counts(company_ids, since, until):
        return {"question_flagged": 4, "question_fixed": 1}

    monkeypatch.setattr(question_updates, "between", found)
    monkeypatch.setattr(question_updates, "counts", counts)

    return asked


def test_the_assistant_gets_each_update_with_its_companys_interviews_link(client, between):
    response = client.post(
        "/internal/questions/updates",
        json=BODY,
        headers=bearer(issue_token("assistant", "library", SECRET)),
    )

    assert response.status_code == 200
    assert between == [(["company-a", "company-b"], SINCE, UNTIL, MAX_UPDATES)]
    # How many of each in all, not only those listed.
    assert response.json()["counts"] == {"question_flagged": 4, "question_fixed": 1}
    flagged, fixed = response.json()["items"]
    assert {key: flagged[key] for key in ("kind", "company_id", "title", "topic", "link")} == {
        "kind": "question_flagged",
        "company_id": "company-a",
        "title": "Backend",
        "topic": "Python",
        "link": "/companies/company-a/interviews",
    }
    assert datetime.fromisoformat(flagged["at"]) == FLAGGED_AT
    assert {key: fixed[key] for key in ("kind", "company_id", "title", "topic", "link")} == {
        "kind": "question_fixed",
        "company_id": "company-b",
        "title": "Frontend",
        "topic": "React",
        "link": "/companies/company-b/interviews",
    }
    assert datetime.fromisoformat(fixed["at"]) == FIXED_AT


@pytest.mark.parametrize("caller", ["generation", "rounds", "companies", "api"])
def test_any_other_service_is_refused(client, between, caller):
    refused = client.post(
        "/internal/questions/updates",
        json=BODY,
        headers=bearer(issue_token(caller, "library", SECRET)),
    )

    assert refused.status_code == 403
    assert refused.json()["detail"] == "Not allowed"
    assert between == []


def test_without_a_service_token_its_refused(client, between):
    assert client.post("/internal/questions/updates", json=BODY).status_code == 401
    assert between == []
