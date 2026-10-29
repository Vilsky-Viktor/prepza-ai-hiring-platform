import asyncio
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException

from api.constants.api import RETRY_FIRST_DELAY
from api.handlers import dispatch
from api.integrations import webhooks as integration
from api.services import accounts
from api.services import webhooks as delivery
from tests.unit.conftest import CANDIDATE, COMPANY, INTERVIEW

HAPPENED = datetime(2026, 10, 15, 8, tzinfo=UTC)
FINISHED = {
    "candidate_invite_id": str(CANDIDATE),
    "interview_id": str(INTERVIEW),
    "company_id": str(COMPANY),
    "title": "Backend",
    "grade": 86,
    "passed": True,
    "flagged": True,
}


def finish(event_id="e1"):
    asyncio.run(delivery.candidate_event("candidate.finished", FINISHED, event_id, HAPPENED))


def test_each_web_hook_gets_the_interview_and_candidate_signed(endpoints):
    endpoints["hook"]("https://a.example/x")
    endpoints["hook"]("https://b.example/x")
    finish()
    (_, body, signature), _ = endpoints["posted"]

    assert sorted(item[0] for item in endpoints["posted"]) == [
        "https://a.example/x",
        "https://b.example/x",
    ]
    assert body["id"] == "e1" and body["type"] == "candidate.finished"
    assert body["data"]["interview"]["id"] == str(INTERVIEW)
    assert body["data"]["candidate"]["grade"] == 86
    assert signature.startswith("t=") and ",v1=" in signature


def test_a_failed_web_hook_is_left_to_the_retry_job_and_the_event_is_done(endpoints):
    endpoints["hook"]("https://a.example/x")
    down = endpoints["hook"]("https://down.example/x")
    endpoints["failing"].add("https://down.example/x")

    # No error: Pub/Sub doesn't send the event again for one company's endpoint.
    finish()
    retry = endpoints["retries"][(down.id, "e1")]
    wait = retry.next_at - datetime.now(UTC)

    assert [item[0] for item in endpoints["posted"]] == ["https://a.example/x"]
    assert list(endpoints["retries"]) == [(down.id, "e1")] and retry.attempts == 1
    assert RETRY_FIRST_DELAY - timedelta(minutes=1) < wait <= RETRY_FIRST_DELAY
    assert '"id":"e1"' in retry.body


def test_a_redelivered_event_reaches_only_the_web_hooks_that_failed_and_keeps_one_retry(
    endpoints,
):
    endpoints["hook"]("https://a.example/x")
    down = endpoints["hook"]("https://down.example/x")
    endpoints["failing"].add("https://down.example/x")
    finish()
    finish()

    assert len(endpoints["posted"]) == 1
    assert endpoints["retries"][(down.id, "e1")].attempts == 1

    endpoints["failing"].clear()
    finish()
    finish()

    assert [item[0] for item in endpoints["posted"]] == [
        "https://a.example/x",
        "https://down.example/x",
    ]


def test_a_web_hook_is_the_companys_whoever_added_it(endpoints, companies_api):
    """One added by a member now a viewer, or gone (their account deleted), still gets events."""
    endpoints["hook"]("https://viewer.example/x", maker="u2")
    endpoints["hook"]("https://gone.example/x", maker=None)
    companies_api["roles"]["u2"] = "viewer"

    finish()

    assert sorted(item[0] for item in endpoints["posted"]) == [
        "https://gone.example/x",
        "https://viewer.example/x",
    ]


def test_without_web_hooks_companies_isnt_asked(endpoints, companies_api):
    companies_api["missing"] = True

    finish()

    assert endpoints["posted"] == []


def test_a_candidate_or_interview_gone_since_tells_nobody(endpoints, companies_api):
    endpoints["hook"]("https://a.example/x")
    companies_api["missing"] = True

    finish()

    assert endpoints["posted"] == []


def test_an_address_no_longer_public_is_skipped(endpoints):
    endpoints["hook"]("https://a.example/x")
    endpoints["public"] = False

    finish()

    assert endpoints["posted"] == []
    assert endpoints["retries"] == {}


def test_an_unreadable_secret_is_retried_so_the_web_hook_shows_as_failing(endpoints, monkeypatch):
    """A key lost from API_ENCRYPTION_KEY: the events wait, and once it's back they go out."""
    hook = endpoints["hook"]("https://a.example/x")
    monkeypatch.setattr(delivery.settings, "api_encryption_key", Fernet.generate_key().decode())

    finish()

    assert endpoints["posted"] == []
    assert list(endpoints["retries"]) == [(hook.id, "e1")]


def test_an_address_that_doesnt_resolve_now_is_retried(endpoints):
    endpoints["hook"]("https://a.example/x")
    flaky = endpoints["hook"]("https://flaky.example/x")
    endpoints["unresolved"].add("https://flaky.example/x")
    finish()

    assert [item[0] for item in endpoints["posted"]] == ["https://a.example/x"]
    assert list(endpoints["retries"]) == [(flaky.id, "e1")]


def test_companies_busy_raises_so_the_event_comes_again(endpoints, monkeypatch):
    endpoints["hook"]("https://a.example/x")
    real = delivery.companies.interview

    async def busy(company_id, interview_id):
        raise HTTPException(503, "Unavailable")

    monkeypatch.setattr(delivery.companies, "interview", busy)

    with pytest.raises(HTTPException):
        finish()

    assert endpoints["posted"] == []

    monkeypatch.setattr(delivery.companies, "interview", real)
    finish()
    finish()

    assert [item[0] for item in endpoints["posted"]] == ["https://a.example/x"]


def test_a_deleted_company_loses_its_keys_and_web_hooks(monkeypatch):
    removed = []

    async def remove_keys(session, company_id):
        removed.append(("keys", company_id))

    async def remove_hooks(session, company_id):
        removed.append(("webhooks", company_id))

    monkeypatch.setattr(accounts.keys, "remove_company", remove_keys)
    monkeypatch.setattr(accounts.webhooks, "remove_company", remove_hooks)
    asyncio.run(dispatch.handle("company.deleted", {"company_id": str(COMPANY)}, "e1"))
    asyncio.run(dispatch.handle("interview.ready", {"interview_id": str(INTERVIEW)}, "e2"))

    assert removed == [("keys", COMPANY), ("webhooks", COMPANY)]


def test_a_send_goes_to_the_checked_address_under_the_hosts_name(monkeypatch):
    """So a lookup that answers differently the second time (DNS rebinding) can't lead it to
    a private address: TLS and the Host header still name the web hook's host."""
    sent = []

    def endpoint(request):
        sent.append(request)

        return httpx.Response(200)

    client = httpx.AsyncClient(transport=httpx.MockTransport(endpoint))
    monkeypatch.setattr(integration, "get_client", lambda: client)
    asyncio.run(integration.post("https://hooks.example:8443/x?a=1", "203.0.113.10", b"{}", "s"))

    assert str(sent[0].url) == "https://203.0.113.10:8443/x?a=1"
    assert sent[0].headers["host"] == "hooks.example:8443"
    assert sent[0].extensions["sni_hostname"] == "hooks.example"
    assert sent[0].headers["prepza-signature"] == "s"


class Endless(httpx.AsyncByteStream):
    """An answer's body that never ends: reading it would never finish."""

    async def __aiter__(self):
        while True:
            yield b"x" * 65536


def test_an_answers_body_is_never_read(monkeypatch):
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=Endless()))
    )
    monkeypatch.setattr(integration, "get_client", lambda: client)

    asyncio.run(integration.post("https://hooks.example/x", "203.0.113.10", b"{}", "s"))


def test_an_endpoint_too_slow_to_answer_fails_within_the_time_limit(monkeypatch):
    async def slow(request):
        await asyncio.sleep(5)

        return httpx.Response(200)

    client = httpx.AsyncClient(transport=httpx.MockTransport(slow))
    monkeypatch.setattr(integration, "get_client", lambda: client)
    monkeypatch.setattr(integration, "WEBHOOK_TIMEOUT_SECONDS", 0.1)

    with pytest.raises(httpx.TimeoutException):
        asyncio.run(integration.post("https://hooks.example/x", "203.0.113.10", b"{}", "s"))


SECRET_URL = "https://hooks.example/in/s3cr3t-token"


def test_a_failed_send_is_logged_without_the_web_hooks_url(endpoints, monkeypatch, caplog):
    endpoints["hook"](SECRET_URL)

    async def refused(url, address, body, signature):
        request = httpx.Request("POST", url)

        raise httpx.HTTPStatusError(
            f"Server error for url {url}", request=request, response=httpx.Response(500)
        )

    monkeypatch.setattr(delivery.endpoints, "post", refused)
    caplog.set_level("INFO")
    finish()

    assert "didn't take e1: 500" in caplog.text
    assert "s3cr3t" not in caplog.text


def test_a_send_isnt_logged_with_its_url(monkeypatch, caplog):
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200)))
    monkeypatch.setattr(integration, "get_client", lambda: client)
    caplog.set_level("INFO", logger="api")
    asyncio.run(integration.post(SECRET_URL, "203.0.113.10", b"{}", "s"))

    assert "s3cr3t" not in caplog.text
