import base64
import json
import uuid

import httpx
import pytest
from prepza_common import http
from prepza_common.ai_constants import LIMIT_HIT

from app.config.settings import settings
from app.helpers.member_emails import digest_email
from app.helpers.unsubscribe import address_hash
from app.services import delivery
from app.storage import opt_outs
from tests.integration.factories import api, push, signed

SECRET = "whsec_" + base64.b64encode(b"test-webhook-key").decode()
INVITE_ID = "6f1c2c1e-0000-4000-8000-000000000001"
INVITE = {
    "email": "bob@example.com",
    "token": "t",
    "title": "Backend",
    "company": "Acme",
    "invite_id": INVITE_ID,
}
PDF = base64.b64encode(b"%PDF-1.3 a report").decode()
REPORT = {
    "email": "boss@example.com",
    "sender": "Bob",
    "reply_to": "bob@example.com",
    "company": "Acme",
    "title": "Backend",
    "candidate": "ann@example.com",
    "language": "en",
    "filename": "Report.pdf",
    "pdf": PDF,
}


@pytest.fixture
def outside(monkeypatch):
    """Resend and the companies service at the HTTP boundary: every request is recorded, and
    Resend answers with `outside["resend"]`."""
    calls = {"requests": [], "resend": 200}

    def answer(request: httpx.Request) -> httpx.Response:
        calls["requests"].append(request)

        if request.url.host == "api.resend.com":
            return httpx.Response(calls["resend"], json={"id": "e-1"})

        return httpx.Response(204)

    monkeypatch.setattr(settings, "resend_api_key", "re_test")
    monkeypatch.setattr(settings, "resend_webhook_secret", SECRET)
    monkeypatch.setattr(settings, "companies_url", "http://companies")
    monkeypatch.setattr(settings, "library_url", "http://library")
    monkeypatch.setattr(
        http, "get_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(answer))
    )

    return calls


def post_events(run, *pushes) -> list[int]:
    async def scenario():
        async with api() as client:
            return [
                (await client.post("/internal/events", json=body)).status_code for body in pushes
            ]

    return run(scenario())


def test_a_shared_report_goes_through_resend_keyed_by_its_event(run, outside):
    codes = post_events(run, push("report.shared", REPORT, outbox_id="outbox-7"))
    [request] = outside["requests"]
    sent = json.loads(request.content)

    assert codes == [204]
    # The same key on every delivery of the event, so Resend sends it once.
    assert request.headers["Idempotency-Key"] == "events/outbox-7"
    assert sent["to"] == ["boss@example.com"]
    assert sent["reply_to"] == "bob@example.com"
    # Named in the email's language: its heading, then the candidate.
    attachment = {"filename": "Candidate report – ann@example.com.pdf", "content": PDF}
    assert sent["attachments"] == [attachment]


def test_a_contact_message_goes_to_the_inbox_and_replies_to_the_visitor(run, outside):
    message = {"name": "Eve", "email": "eve@example.com", "language": "en", "message": "Hi"}
    post_events(run, push("contact.sent", message, message_id="pubsub-9"))
    [request] = outside["requests"]
    sent = json.loads(request.content)

    # Without an outbox id, Pub/Sub's message id is the key.
    assert request.headers["Idempotency-Key"] == "events/pubsub-9"
    assert (sent["to"], sent["reply_to"]) == ([settings.contact_email], "eve@example.com")


def test_a_failing_resend_answers_with_an_error_so_pub_sub_retries(run, outside):
    outside["resend"] = 503

    assert post_events(run, push("report.shared", REPORT)) == [500]


def test_a_burst_over_resends_limit_is_retried_without_a_server_error(run, outside, published):
    outside["resend"] = 429
    busy = post_events(run, push("candidate.invited", INVITE, outbox_id="outbox-9"))
    outside["resend"] = 200
    retried = post_events(run, push("candidate.invited", INVITE, outbox_id="outbox-9"))
    keys = {request.headers["Idempotency-Key"] for request in outside["requests"]}

    # Pub/Sub retries a 429 with backoff; the retry sends it, under the same key.
    assert (busy, retried) == ([429], [204])
    assert keys == {"events/outbox-9"}
    # Resend's limit is recorded as its own.
    assert [(data["limit"], data["kind"]) for kind, data in published if kind == LIMIT_HIT] == [
        ("RESEND_RATE_LIMIT", "provider:resend")
    ]


def test_an_invite_resend_refuses_is_marked_undelivered_and_not_retried(run, outside):
    outside["resend"] = 422

    assert post_events(run, push("candidate.invited", INVITE)) == [204]
    assert [str(request.url) for request in outside["requests"][1:]] == [
        f"http://companies/internal/invites/{INVITE_ID}/undelivered"
    ]


def bounce() -> bytes:
    tags = {"kind": "candidate_invite", "id": INVITE_ID}

    return json.dumps({"type": "email.bounced", "data": {"tags": tags}}).encode()


def test_a_signed_bounce_marks_the_invite_undelivered(run, outside):
    async def scenario():
        async with api() as client:
            return await client.post(
                "/webhooks/resend", content=bounce(), headers=signed(bounce(), SECRET)
            )

    response = run(scenario())
    [request] = outside["requests"]

    assert response.status_code == 204
    assert str(request.url) == f"http://companies/internal/invites/{INVITE_ID}/undelivered"
    assert request.headers["Authorization"].startswith("Bearer ")


def test_after_a_hard_bounce_no_invite_goes_to_the_address_and_it_shows_undelivered(run, outside):
    address = f"b{uuid.uuid4().hex[:12]}@example.com"
    tags = {"kind": "candidate_invite", "id": INVITE_ID}
    body = json.dumps(
        {"type": "email.bounced", "data": {"to": [address], "tags": tags, "bounce": {}}}
    ).encode()

    async def scenario():
        async with api() as client:
            await client.post("/webhooks/resend", content=body, headers=signed(body, SECRET))

    run(scenario())
    codes = post_events(run, push("candidate.invited", {**INVITE, "email": address}))
    undelivered = f"http://companies/internal/invites/{INVITE_ID}/undelivered"

    assert codes == [204]
    # The bounce's report, then the next invite's: Resend is never asked to send it.
    assert [str(request.url) for request in outside["requests"]] == [undelivered, undelivered]


def test_a_spam_complaint_on_a_reminder_stops_only_that_invites_reminders(run, outside):
    address = f"c{uuid.uuid4().hex[:12]}@example.com"
    company = str(uuid.uuid4())
    tags = {"kind": "candidate_reminder", "id": INVITE_ID, "company": company}
    body = json.dumps({"type": "email.complained", "data": {"to": [address], "tags": tags}})

    async def scenario():
        async with api() as client:
            await client.post(
                "/webhooks/resend", content=body, headers=signed(body.encode(), SECRET)
            )

        hashed = address_hash(address)

        return (
            await opt_outs.opted_out(hashed, company, INVITE_ID),
            await opt_outs.opted_out(hashed, company),
        )

    assert run(scenario()) == (True, False)


def test_a_webhook_with_a_wrong_signature_is_refused(run, outside):
    async def scenario():
        async with api() as client:
            headers = signed(bounce(), "whsec_" + base64.b64encode(b"another-key").decode())

            return await client.post("/webhooks/resend", content=bounce(), headers=headers)

    assert run(scenario()).status_code == 401
    assert outside["requests"] == []


def test_a_spam_complaint_on_a_sent_digest_turns_the_digest_off_in_library(run, outside):
    recipient = {"user_id": "ann", "email": "ann@example.com", "language": "en"}
    email = digest_email(recipient, [], "http://localhost:8090", settings.email_link_secret)

    async def scenario():
        await delivery.send(email, "digest/ann/1")
        [request] = outside["requests"]
        sent = json.loads(request.content)
        # Resend's webhook carries back the tags the email was sent with.
        tags = {tag["name"]: tag["value"] for tag in sent["tags"]}
        body = json.dumps({"type": "email.complained", "data": {"tags": tags}}).encode()

        async with api() as client:
            response = await client.post(
                "/webhooks/resend", content=body, headers=signed(body, SECRET)
            )

        return sent, response

    sent, response = run(scenario())
    unsubscribe = outside["requests"][1]

    assert sent["from"] == settings.mail_from_updates
    assert response.status_code == 204
    assert str(unsubscribe.url) == "http://library/internal/users/ann/unsubscribe"
    assert json.loads(unsubscribe.content) == {
        "settings": [
            "candidate_finished",
            "invite_undelivered",
            "ats_not_invited",
            "interview_ready",
        ]
    }
