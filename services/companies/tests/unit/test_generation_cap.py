import uuid
from datetime import UTC, datetime

import httpx
import pytest
from fake_redis import FakeRedis
from prepza_common import ai_cap
from prepza_common.auth import current_user
from prepza_common.user import User

from app.integrations import billing, generation
from app.main import app
from app.models.companies import Company, Member
from app.models.interviews import Interview
from app.routers import interview_generation
from app.storage import audit, companies, interview_generations, interviews

COMPANY_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()
PATHS = [
    f"/interviews/{INTERVIEW_ID}/generation/review",
    f"/interviews/{INTERVIEW_ID}/generation/retry",
]
AI_PAUSED_TODAY = (
    "AI features are paused for today. They're back tomorrow, or right away for companies that "
    "have topped up."
)


@pytest.fixture
def generating(monkeypatch):
    """Bob owns Acme, whose interview is being generated; returns Redis (today's unpaid AI spend
    and the limits), whether Acme `paid`, and the calls that reached generation."""
    redis = FakeRedis()
    state = {"redis": redis, "paid": False, "reached": []}
    company = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC))
    company.members = [Member(company_id=COMPANY_ID, user_id="bob", role="owner")]
    interview = Interview(id=INTERVIEW_ID, company_id=COMPANY_ID, generation_id=uuid.uuid4())

    async def get_interview(_interview_id):
        return interview

    async def get_company(_company_id):
        return company

    async def paid(_company_id):
        return state["paid"]

    async def generate(*args):
        state["reached"].append(args[0])

        return httpx.Response(200, json={"status": "generating"})

    async def nothing(*args, **kwargs):
        return None

    monkeypatch.setattr(interviews, "get", get_interview)
    monkeypatch.setattr(companies, "get", get_company)
    monkeypatch.setattr(billing, "company_paid", paid)
    monkeypatch.setattr(generation, "review", generate)
    monkeypatch.setattr(generation, "retry", generate)
    monkeypatch.setattr(interview_generation, "get_redis", lambda: redis)
    monkeypatch.setattr(interview_generations, "set_generation_failed", nothing)
    # The action log isn't what these tests check.
    monkeypatch.setattr(audit, "record_interview", nothing)
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True
    )
    yield state
    app.dependency_overrides.clear()


def spent_today(state, micro_usd):
    state["redis"].counts[ai_cap.today_key()] = micro_usd


@pytest.mark.parametrize("path", PATHS)
def test_an_unpaid_companys_generation_stops_once_today_reached_the_cap(
    client, generating, limit_hits, path
):
    spent_today(generating, 14_999_999)
    allowed = client.post(path, json={"selected": [0]})
    spent_today(generating, 15_000_000)
    refused = client.post(path, json={"selected": [0]})

    assert allowed.status_code == 200
    assert refused.status_code == 503
    assert refused.json() == {"detail": AI_PAUSED_TODAY}
    assert len(generating["reached"]) == 1
    assert [(hit["limit"], hit["company_id"], hit["user_id"]) for hit in limit_hits] == [
        ("AI_SPEND_UNPAID_DAY", str(COMPANY_ID), "bob")
    ]


@pytest.mark.parametrize("path", PATHS)
def test_the_cap_is_as_edited(client, generating, path):
    generating["redis"].limits["AI_SPEND_UNPAID_DAY"] = "2.5"
    spent_today(generating, 2_500_000)
    refused = client.post(path, json={"selected": [0]})

    assert refused.status_code == 503
    assert refused.json() == {"detail": AI_PAUSED_TODAY}
    assert generating["reached"] == []


@pytest.mark.parametrize("path", PATHS)
def test_a_paid_companys_generation_goes_on_past_the_cap(client, generating, limit_hits, path):
    generating["paid"] = True
    spent_today(generating, 100_000_000)
    response = client.post(path, json={"selected": [0]})

    assert response.status_code == 200
    assert len(generating["reached"]) == 1
    assert limit_hits == []
