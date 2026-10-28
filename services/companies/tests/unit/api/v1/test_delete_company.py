import uuid
from datetime import UTC, datetime

import httpx
import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User

from companies.integrations import billing, generation, library, rounds
from companies.main import app
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.repositories import companies, interview_generations, interviews

COMPANY_ID = uuid.uuid4()
READY_SET_ID = uuid.uuid4()
FINISHED_SET_ID = uuid.uuid4()
GENERATING_ID = uuid.uuid4()
FINISHING_ID = uuid.uuid4()
URL = f"/companies/{COMPANY_ID}"


def interview(generation_id, set_id):
    return Interview(
        id=uuid.uuid4(),
        company_id=COMPANY_ID,
        generation_id=generation_id,
        set_id=set_id,
        generation_failed=False,
    )


@pytest.fixture
def calls(monkeypatch):
    """A ready interview, one still generating and one that finishes while it's cancelled."""
    recorded = []
    company = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC))
    company.members = [
        Member(company_id=COMPANY_ID, user_id="bob", invited_email="bob@example.com", role="owner"),
    ]

    async def fake_company(_company_id):
        return company

    async def fake_list(_company_id, after, limit):
        # One page, then none.
        if after is not None:
            return []

        return [
            interview(uuid.uuid4(), READY_SET_ID),
            interview(GENERATING_ID, None),
            interview(FINISHING_ID, None),
        ]

    async def fake_cancel(generation_id, _company_id):
        recorded.append(("cancel", generation_id))

        return httpx.Response(409 if generation_id == FINISHING_ID else 200)

    async def fake_get(generation_id, _company_id):
        return {"preparation_id": FINISHED_SET_ID if generation_id == FINISHING_ID else None}

    async def fake_set_id(_interview_id, _set_id):
        return None

    async def fake_rounds(set_id):
        recorded.append(("rounds", set_id))

    async def fake_library(set_id):
        recorded.append(("library", set_id))

    async def fake_delete(company_id):
        recorded.append(("company", company_id))

    async def fake_billing(company_id):
        recorded.append(("billing", company_id))

    monkeypatch.setattr(companies, "get", fake_company)
    monkeypatch.setattr(interviews, "page_by_id", fake_list)
    monkeypatch.setattr(generation, "cancel", fake_cancel)
    monkeypatch.setattr(generation, "get", fake_get)
    monkeypatch.setattr(interview_generations, "set_set_id", fake_set_id)
    monkeypatch.setattr(rounds, "delete_interview_data", fake_rounds)
    monkeypatch.setattr(library, "delete_interview", fake_library)
    monkeypatch.setattr(companies, "delete", fake_delete)
    monkeypatch.setattr(billing, "delete_company", fake_billing)
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True, name="bob"
    )

    yield recorded

    app.dependency_overrides.clear()


def test_cleans_up_every_interview_before_the_company(client, calls):
    assert client.delete(URL).status_code == 204
    assert calls == [
        ("rounds", READY_SET_ID),
        ("library", READY_SET_ID),
        ("cancel", GENERATING_ID),
        ("cancel", FINISHING_ID),
        ("rounds", FINISHED_SET_ID),
        ("library", FINISHED_SET_ID),
        ("billing", COMPANY_ID),
        ("company", COMPANY_ID),
    ]


def test_a_failed_cleanup_keeps_the_company(client, calls, monkeypatch):
    async def failing_library(_set_id):
        request = httpx.Request("DELETE", "http://library")

        raise httpx.HTTPStatusError("down", request=request, response=httpx.Response(503))

    monkeypatch.setattr(library, "delete_interview", failing_library)

    with pytest.raises(httpx.HTTPStatusError):
        client.delete(URL)

    assert ("company", COMPANY_ID) not in calls


def test_a_failed_billing_cleanup_keeps_the_company_to_delete_again(client, calls, monkeypatch):
    """Otherwise a retry finds no company, and its automatic top-up's saved card stays."""

    async def failing_billing(_company_id):
        request = httpx.Request("DELETE", "http://billing")

        raise httpx.HTTPStatusError("down", request=request, response=httpx.Response(503))

    monkeypatch.setattr(billing, "delete_company", failing_billing)

    with pytest.raises(httpx.HTTPStatusError):
        client.delete(URL)

    assert ("company", COMPANY_ID) not in calls
