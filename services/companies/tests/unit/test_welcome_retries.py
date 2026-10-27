import asyncio
import uuid

import httpx
import pytest
from prepza_common.http import http

from app.constants.billing import WELCOME_ATTEMPTS, WELCOME_FIRST_WAIT_SECONDS
from app.integrations import billing

# The real call: conftest replaces billing.welcome_company for the other tests.
from app.integrations.billing import welcome_company


def answering(*codes):
    """A billing that answers each call with the next status code; returns the calls made."""
    calls = []

    def handler(request):
        calls.append(request.url.path)

        return httpx.Response(codes[len(calls) - 1])

    return httpx.AsyncClient(transport=httpx.MockTransport(handler)), calls


@pytest.fixture(autouse=True)
def waits(monkeypatch):
    """The waits between tries, recorded instead of slept."""
    slept = []

    async def sleep(seconds):
        slept.append(seconds)

    monkeypatch.setattr(billing.asyncio, "sleep", sleep)

    return slept


def test_a_welcome_whose_answer_was_lost_is_asked_again_for_the_same_company(monkeypatch, waits):
    client, calls = answering(503, 204)
    monkeypatch.setattr(http, "get_client", lambda: client)
    company_id = uuid.uuid4()

    asyncio.run(welcome_company(company_id, "ann@example.com", None, [], None))

    assert calls == [f"/internal/companies/{company_id}/welcome"] * 2
    # It waited before asking again, not at once.
    assert len(waits) == 1 and 0 <= waits[0] <= WELCOME_FIRST_WAIT_SECONDS


def test_a_welcome_failing_every_time_fails_after_its_tries(monkeypatch):
    client, calls = answering(*[503] * WELCOME_ATTEMPTS)
    monkeypatch.setattr(http, "get_client", lambda: client)

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(welcome_company(uuid.uuid4(), "ann@example.com", None, [], None))

    assert len(calls) == WELCOME_ATTEMPTS


def test_a_welcome_billing_refuses_isnt_asked_again(monkeypatch, waits):
    client, calls = answering(422, 204)
    monkeypatch.setattr(http, "get_client", lambda: client)

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(welcome_company(uuid.uuid4(), "ann@example.com", None, [], None))

    assert (len(calls), waits) == (1, [])
