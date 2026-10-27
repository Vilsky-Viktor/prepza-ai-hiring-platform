import asyncio
import uuid

import httpx
import pytest
from fastapi import HTTPException
from prepza_common.auth import company_invites
from prepza_common.http import http
from prepza_common.http.http import bearer, passed_on
from prepza_common.observability.logging import trace_header


def answer(code: int, body=None) -> httpx.Response:
    return httpx.Response(code, json=body, request=httpx.Request("GET", "http://x"))


def test_a_refusal_asked_for_reaches_the_client_with_its_reason():
    with pytest.raises(HTTPException) as refused:
        passed_on(answer(402, {"detail": "Not enough credits."}), {402, 409})

    assert (refused.value.status_code, refused.value.detail) == (402, "Not enough credits.")


def test_a_refusal_keeps_its_machine_readable_code():
    with pytest.raises(HTTPException) as refused:
        passed_on(answer(409, {"detail": "Not ready.", "code": "interview_not_ready"}), {409})
    with pytest.raises(HTTPException) as uncoded:
        passed_on(answer(409, {"detail": "Not ready."}), {409})

    assert (refused.value.detail, refused.value.code) == ("Not ready.", "interview_not_ready")
    assert getattr(uncoded.value, "code", None) is None


def test_a_rate_limits_refusal_keeps_its_retry_after():
    limited = httpx.Response(
        429,
        json={"detail": "Too many requests."},
        headers={"Retry-After": "42"},
        request=httpx.Request("GET", "http://x"),
    )

    with pytest.raises(HTTPException) as refused:
        passed_on(limited, {429})

    assert refused.value.headers == {"Retry-After": "42"}

    with pytest.raises(HTTPException) as other:
        passed_on(answer(402, {"detail": "Not enough credits."}))

    assert other.value.headers is None


def test_any_refusal_passes_without_codes_and_others_raise_with_them():
    with pytest.raises(HTTPException):
        passed_on(answer(422, {"detail": "Invalid"}))

    with pytest.raises(httpx.HTTPStatusError):
        passed_on(answer(500), {402})

    assert passed_on(answer(200, {"ok": True})).json() == {"ok": True}


def test_an_invite_through_companies_returns_its_id_or_its_refusal(monkeypatch):
    made = uuid.uuid4()
    answers = iter(
        [
            httpx.Response(201, json={"invite_id": str(made), "created": True}),
            httpx.Response(201, json={"invite_id": str(made), "created": False}),
            httpx.Response(409, json={"detail": "Interview is still being generated"}),
        ]
    )
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: next(answers)))
    monkeypatch.setattr(http, "get_client", lambda: client)
    body = {"email": "ann@example.com", "sender_id": "u1"}

    found = asyncio.run(company_invites.invite("http://companies", "t", made, body, {409}))
    again = asyncio.run(company_invites.invite("http://companies", "t", made, body, {409}))

    assert found == (made, True)
    # Already invited and returned as they were.
    assert again == (made, False)
    with pytest.raises(HTTPException) as refused:
        asyncio.run(company_invites.invite("http://companies", "t", made, body, {409}))
    assert refused.value.detail == "Interview is still being generated"


def test_a_token_goes_in_the_authorization_header():
    assert bearer("t0ken") == {"Authorization": "Bearer t0ken"}


def test_a_call_made_while_serving_a_request_carries_its_trace():
    request = httpx.Request("GET", "http://library/internal/x")
    token = trace_header.set("abc123/1;o=1")

    try:
        asyncio.run(http.pass_trace(request))
    finally:
        trace_header.reset(token)

    assert request.headers["X-Cloud-Trace-Context"] == "abc123/1;o=1"
    assert http.pass_trace in http.get_client().event_hooks["request"]


def test_a_call_outside_any_request_carries_no_trace():
    request = httpx.Request("GET", "http://library/internal/x")
    asyncio.run(http.pass_trace(request))

    assert "X-Cloud-Trace-Context" not in request.headers
