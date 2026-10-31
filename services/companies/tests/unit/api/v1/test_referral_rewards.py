import uuid
from datetime import UTC, datetime

from testee_common.auth.auth import current_user
from testee_common.auth.user import User

from companies.integrations import billing
from companies.main import app
from companies.models.companies import Company, Member
from companies.repositories import companies

COMPANY_ID = uuid.uuid4()
JOINED = str(uuid.uuid4())
GONE = str(uuid.uuid4())


def test_the_referral_lists_rewarded_companies_by_name(client, monkeypatch):
    company = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC))
    company.members = [
        Member(
            company_id=COMPANY_ID,
            user_id="bob",
            invited_email="bob@example.com",
            role="viewer",
            created_at=datetime.now(UTC),
        )
    ]

    async def get_company(session, _company_id):
        return company

    async def referral(_company_id):
        return {
            "code": "abc",
            "reward": 500,
            "rewarded": 2,
            "rewards": [
                {"company_id": JOINED, "rewarded_at": "2026-10-05T10:00:00Z", "credits": 1000},
                {"company_id": GONE, "rewarded_at": "2026-10-01T10:00:00Z", "credits": 0},
            ],
        }

    async def names(session, company_ids):
        return {JOINED: "Globex"}

    monkeypatch.setattr(companies, "get", get_company)
    monkeypatch.setattr(companies, "names", names)
    monkeypatch.setattr(billing, "company_referral", referral)
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True
    )

    try:
        found = client.get(f"/companies/{COMPANY_ID}/referral").json()
    finally:
        app.dependency_overrides.clear()

    assert found["rewarded"] == 2
    # A deleted company keeps its row, without a name.
    assert [row["name"] for row in found["rewards"]] == ["Globex", None]
    # Each at what it gave then (an earlier reward, or none over the yearly limit), not today's.
    assert [row["credits"] for row in found["rewards"]] == [1000, 0]
