import pytest
from fake_redis import FakeRedis
from sqlalchemy.exc import IntegrityError

from companies.constants.invites import COMPANY_NAME_TAKEN
from companies.repositories import companies
from companies.services import company_creation as company_routes
from tests.unit.api.v1.test_companies import sign_in


@pytest.mark.parametrize(("edited", "most"), [(None, 3), (5, 5)])
def test_nobody_creates_more_companies_than_one_person_may_own(
    client, monkeypatch, limit_hits, edited, most
):
    owned = {"count": most}
    redis = FakeRedis({"MAX_OWNED_COMPANIES": edited} if edited else None)

    async def owned_count(session, user_id):
        return owned["count"]

    async def name_taken(session, name, user_id, email, most=None):
        raise IntegrityError("INSERT", {}, Exception(companies.NAME_INDEX))

    async def no_track(*args, **kwargs):
        return None

    monkeypatch.setattr(company_routes, "get_redis", lambda: redis)
    monkeypatch.setattr(company_routes, "track", no_track)
    monkeypatch.setattr(companies, "owned_count", owned_count)
    monkeypatch.setattr(companies, "create", name_taken)
    sign_in()
    refused = client.post("/companies", json={"name": "Acme"})
    owned["count"] = most - 1
    # Under the limit, the company is made: its name being taken is the next refusal.
    allowed = client.post("/companies", json={"name": "Acme"})

    assert refused.status_code == 409
    assert refused.json() == {
        "detail": f"You already own as many companies as one person may: {most}."
    }
    assert allowed.status_code == 409
    assert allowed.json() == {"detail": COMPANY_NAME_TAKEN}
    assert [(hit["limit"], hit["company_id"], hit["user_id"]) for hit in limit_hits] == [
        ("MAX_OWNED_COMPANIES", None, "bob")
    ]
