import asyncio
import json
import uuid

import httpx
import jwt
import pytest
from fastapi import HTTPException
from prepza_common.http import http

from ats.integrations import companies

COMPANY_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()
SECRET = "test-secret-that-is-at-least-32-bytes"


@pytest.fixture
def answering(monkeypatch):
    """Companies answering with `answer(request)`; every request it got is kept."""
    seen = []

    def use(answer):
        def handler(request):
            seen.append(request)

            return answer(request)

        monkeypatch.setattr(
            http, "get_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler))
        )

        return seen

    return use


def signed_by_ats(request) -> bool:
    token = request.headers["Authorization"].removeprefix("Bearer ")
    claims = jwt.decode(token, SECRET, algorithms=["HS256"], audience="companies")

    return claims["iss"] == "ats"


def test_access_asks_companies_as_ats_for_the_users_role(answering):
    seen = answering(lambda request: httpx.Response(200, json={"member": True, "editor": False}))

    found = asyncio.run(companies.access(COMPANY_ID, "ann"))

    assert found == {"member": True, "editor": False}
    [request] = seen
    assert request.url.path == f"/internal/companies/{COMPANY_ID}/access"
    assert request.url.params["user_id"] == "ann"
    assert signed_by_ats(request)


def test_a_company_that_doesnt_exist_has_no_members(answering):
    answering(lambda request: httpx.Response(404, json={"detail": "Company not found"}))

    assert asyncio.run(companies.access(COMPANY_ID, "ann")) == {"member": False, "editor": False}


def test_interviews_come_in_one_call_by_id(answering):
    other = uuid.uuid4()
    item = {"id": str(INTERVIEW_ID), "company_id": str(COMPANY_ID), "title": "A", "ready": True}
    seen = answering(lambda request: httpx.Response(200, json=[item]))

    found = asyncio.run(companies.interviews([INTERVIEW_ID, other]))

    assert found == {INTERVIEW_ID: item}
    [request] = seen
    assert request.url.params.get_list("ids") == [str(INTERVIEW_ID), str(other)]
    # None asked: no call.
    assert asyncio.run(companies.interviews(set())) == {} and len(seen) == 1


def test_an_invite_is_sent_as_whoever_connected_and_returns_its_id(answering):
    invite_id = uuid.uuid4()
    seen = answering(lambda request: httpx.Response(201, json={"invite_id": str(invite_id)}))

    assert asyncio.run(companies.invite(INTERVIEW_ID, "a@x.com", "ann")) == invite_id
    [request] = seen
    assert request.url.path == f"/internal/interviews/{INTERVIEW_ID}/invites"
    assert json.loads(request.content) == {"email": "a@x.com", "sender_id": "ann", "name": None}
    assert signed_by_ats(request)


@pytest.mark.parametrize("refusal", [402, 404, 409, 429, 503])
def test_a_refused_invite_raises_with_companies_status(answering, refusal):
    answering(lambda request: httpx.Response(refusal, json={"detail": "No"}))

    with pytest.raises(HTTPException) as raised:
        asyncio.run(companies.invite(INTERVIEW_ID, "a@x.com", "ann"))

    assert raised.value.status_code == refusal


def test_a_failing_companies_is_an_error_not_a_refusal(answering):
    answering(lambda request: httpx.Response(500))

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(companies.invite(INTERVIEW_ID, "a@x.com", "ann"))
