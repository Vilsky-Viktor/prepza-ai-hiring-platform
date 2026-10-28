import uuid
from datetime import UTC, datetime

import httpx
import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User
from prepza_common.http import http

from companies.integrations import generation
from companies.main import app
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.repositories import companies, interviews
from companies.services import company_deletion

COMPANY_ID = uuid.uuid4()
READY_SET = uuid.uuid4()
GENERATING = uuid.uuid4()


@pytest.fixture(autouse=True)
def owner(monkeypatch):
    company = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC))
    company.members = [
        Member(company_id=COMPANY_ID, user_id="bob", invited_email="bob@example.com", role="owner")
    ]

    async def fake_get(session, _company_id):
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


def record_calls(monkeypatch, listed, cancel_status=200):
    """Records every step in order; the still-generating interview has no set. Every service
    but generation answers 503, as if rounds and library were down."""
    calls = []

    def down(request):
        calls.append(("call", request.url.host))

        return httpx.Response(503)

    client = httpx.AsyncClient(transport=httpx.MockTransport(down))
    monkeypatch.setattr(http, "get_client", lambda: client)

    async def fake_list(session, _company_id, after, limit):
        # One page, then none.
        return listed if after is None else []

    async def fake_cancel(generation_id, company_id):
        calls.append(("cancel", generation_id))

        return httpx.Response(cancel_status, request=httpx.Request("POST", "http://generation"))

    async def fake_attach(item):
        return item

    async def fake_delete(session, company_id):
        calls.append(("company", company_id))

    monkeypatch.setattr(interviews, "page_by_id", fake_list)
    monkeypatch.setattr(generation, "cancel", fake_cancel)
    monkeypatch.setattr(company_deletion, "attach_set", fake_attach)
    monkeypatch.setattr(companies, "delete", fake_delete)

    return calls


def test_a_company_is_deleted_while_rounds_and_library_are_down(client, monkeypatch):
    """Generations stop first; results and questions go with the interviews' and the company's
    events, so neither service is called."""
    calls = record_calls(monkeypatch, [interview(READY_SET), interview(None, GENERATING)])

    assert client.delete(f"/companies/{COMPANY_ID}").status_code == 204
    assert calls == [("cancel", GENERATING), ("company", COMPANY_ID)]


def test_a_failed_cancel_keeps_the_company_to_delete_again(client, monkeypatch):
    calls = record_calls(monkeypatch, [interview(None, GENERATING)], cancel_status=503)

    with pytest.raises(httpx.HTTPStatusError):
        client.delete(f"/companies/{COMPANY_ID}")

    assert ("company", COMPANY_ID) not in calls
