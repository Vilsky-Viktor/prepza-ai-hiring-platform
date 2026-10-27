import uuid
from datetime import UTC, datetime

import httpx
import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User

from app.integrations import generation, library, rounds
from app.main import app
from app.models.companies import Company, Member
from app.models.interviews import Interview
from app.services import company_deletion
from app.storage import companies, interviews

COMPANY_ID = uuid.uuid4()
READY_SET = uuid.uuid4()
GENERATING = uuid.uuid4()


@pytest.fixture(autouse=True)
def owner(monkeypatch):
    company = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC))
    company.members = [
        Member(company_id=COMPANY_ID, user_id="bob", invited_email="bob@example.com", role="owner")
    ]

    async def fake_get(_company_id):
        return company

    monkeypatch.setattr(companies, "get", fake_get)
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True
    )

    yield

    app.dependency_overrides.clear()


def interview(set_id, generation_id=None):
    return Interview(
        id=uuid.uuid4(),
        company_id=COMPANY_ID,
        generation_id=generation_id or uuid.uuid4(),
        set_id=set_id,
    )


def record_calls(monkeypatch, listed, fail_library=False):
    """Records every cleanup call in order; the still-generating interview has no set."""
    calls = []

    async def fake_list(_company_id, after, limit):
        # One page, then none.
        return listed if after is None else []

    async def fake_cancel(generation_id, company_id):
        calls.append(("cancel", generation_id))

        return httpx.Response(200, request=httpx.Request("POST", "http://generation"))

    async def fake_attach(item):
        return item

    async def fake_rounds(set_id):
        calls.append(("rounds", set_id))

    async def fake_library(set_id):
        calls.append(("library", set_id))

        if fail_library:
            raise httpx.ConnectError("library is down")

    async def fake_delete(company_id):
        calls.append(("company", company_id))

    monkeypatch.setattr(interviews, "page_by_id", fake_list)
    monkeypatch.setattr(generation, "cancel", fake_cancel)
    monkeypatch.setattr(company_deletion, "attach_set", fake_attach)
    monkeypatch.setattr(rounds, "delete_interview_data", fake_rounds)
    monkeypatch.setattr(library, "delete_interview", fake_library)
    monkeypatch.setattr(companies, "delete", fake_delete)

    return calls


def test_interviews_are_cleaned_up_before_the_company_is_deleted(client, monkeypatch):
    calls = record_calls(monkeypatch, [interview(READY_SET), interview(None, GENERATING)])

    assert client.delete(f"/companies/{COMPANY_ID}").status_code == 204
    assert calls == [
        ("rounds", READY_SET),
        ("library", READY_SET),
        ("cancel", GENERATING),
        ("company", COMPANY_ID),
    ]


def test_failed_cleanup_keeps_the_company_to_delete_again(client, monkeypatch):
    calls = record_calls(monkeypatch, [interview(READY_SET)], fail_library=True)

    with pytest.raises(httpx.ConnectError):
        client.delete(f"/companies/{COMPANY_ID}")

    assert ("company", COMPANY_ID) not in calls
