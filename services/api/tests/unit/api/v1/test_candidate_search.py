"""A candidate is found by email in a POST body; the query-string way still works until its
sunset and says so."""

from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

# The key fixture is imported from test_public_routes and named in the tests.
# ruff: noqa: F811
import pytest

from api.config import settings
from api.integrations import companies
from api.main import app
from tests.unit.api.v1.test_public_routes import call, key  # noqa: F401 (fixture)
from tests.unit.conftest import CANDIDATE, INTERVIEW, candidate


@pytest.fixture
def asked(monkeypatch):
    emails = []

    async def find(company_id, email):
        emails.append(email)

        return [candidate(interview_id=str(INTERVIEW))]

    monkeypatch.setattr(companies, "find_candidates", find)

    return emails


def test_the_email_goes_in_the_body_and_nothing_says_deprecated(client, companies_api, key, asked):
    response = call(client, "POST", "/candidates/search", json={"email": "anna@example.com"})

    assert response.status_code == 200
    assert [(row["id"], row["interview_id"]) for row in response.json()] == [
        (str(CANDIDATE), str(INTERVIEW))
    ]
    assert asked == ["anna@example.com"]
    assert "Deprecation" not in response.headers
    assert response.headers["Cache-Control"] == "no-store"


def test_the_query_string_way_still_answers_and_names_its_sunset(client, companies_api, key, asked):
    response = call(client, "GET", "/candidates", params={"email": "anna@example.com"})

    assert [row["id"] for row in response.json()] == [str(CANDIDATE)]
    deprecated_at = int(response.headers["Deprecation"].removeprefix("@"))
    sunset = parsedate_to_datetime(response.headers["Sunset"])
    assert datetime.fromtimestamp(deprecated_at, UTC) == datetime(2026, 10, 22, tzinfo=UTC)
    # At least six months' notice.
    assert (sunset - datetime(2026, 10, 22, tzinfo=UTC)).days >= 182
    assert response.headers["Link"] == (
        f'<{settings.site_url}/api-docs>; rel="deprecation"; type="text/html"'
    )


def test_the_reference_marks_the_query_string_way_deprecated():
    paths = app.openapi()["paths"]

    assert paths["/candidates"]["get"]["deprecated"] is True
    assert "deprecated" not in paths["/candidates/search"]["post"]
