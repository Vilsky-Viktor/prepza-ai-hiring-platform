import pytest

from companies.constants.bias_audit import NOT_OWNER
from companies.repositories import companies
from companies.services import bias_audit
from tests.unit.api.v1.test_audit import company_of, sign_in
from tests.unit.api.v1.test_candidates import COMPANY_ID

URL = f"/companies/{COMPANY_ID}/bias-audit"


@pytest.fixture
def exported(monkeypatch):
    """The export's service answered in memory; returns what it was asked for."""
    asked = []

    async def fake_export(company, user_id, interview_id, start, end):
        asked.append((company.id, user_id, interview_id, start, end))

        return "candidate_id\n"

    monkeypatch.setattr(bias_audit, "export", fake_export)

    return asked


def as_role(monkeypatch, role):
    company = company_of(role)

    async def fake_company(session, _company_id):
        return company

    monkeypatch.setattr(companies, "get", fake_company)
    sign_in("bob")


@pytest.mark.parametrize("role", ["admin", "viewer"])
def test_only_the_owner_exports(client, monkeypatch, exported, role):
    as_role(monkeypatch, role)

    response = client.get(URL)

    assert (response.status_code, response.json()["detail"]) == (403, NOT_OWNER)
    assert exported == []


def test_the_owner_gets_a_csv_file_never_cached(client, monkeypatch, exported):
    as_role(monkeypatch, "owner")

    response = client.get(
        URL, params={"from": "2026-10-01T00:00:00Z", "to": "2026-10-31T00:00:00Z"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"].startswith(
        'attachment; filename="prepza-bias-audit-'
    )
    assert response.headers["cache-control"] == "no-store"
    assert response.text == "candidate_id\n"
    [(company_id, user_id, interview_id, start, end)] = exported
    assert (company_id, user_id, interview_id) == (COMPANY_ID, "bob", None)
    assert (start.isoformat(), end.isoformat()) == (
        "2026-10-01T00:00:00+00:00",
        "2026-10-31T00:00:00+00:00",
    )


def test_someone_outside_the_company_finds_nothing(client, monkeypatch, exported):
    as_role(monkeypatch, "owner")
    sign_in("mallory")

    assert client.get(URL).status_code == 404
    assert exported == []
