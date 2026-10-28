import asyncio

import httpx
import pytest
from event_pushes import push
from prepza_common.config.constants import LANGUAGES

from notifications.config import settings
from notifications.helpers.emails import candidate_invite_email, contact_email
from notifications.integrations import companies, resend, smtp
from notifications.templates.emails import EMAILS

DATA = {"email": "bob@example.com", "token": "abc", "title": "Backend", "company": "Acme"}


@pytest.fixture(autouse=True)
def emulator(monkeypatch):
    monkeypatch.setenv("PUBSUB_EMULATOR_HOST", "pubsub:8085")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "demo-test")


def test_candidate_invite_email():
    data = {
        "email": "bob@example.com",
        "token": "xyz",
        "title": "Backend",
        "company": "Acme",
    }
    email = candidate_invite_email(data, "http://localhost:8090", "secret")

    assert email.to == "bob@example.com"
    assert "Acme" in email.subject
    assert "http://localhost:8090/invite/xyz" in email.text
    assert 'href="http://localhost:8090/invite/xyz"' in email.html
    assert "Acme invited you to the “Backend” interview on prepza." in email.text
    assert ">Acme</strong> invited you" in email.html


def test_html_escapes_names_and_titles():
    email = candidate_invite_email(
        {**DATA, "company": "<b>Acme</b>"}, "http://localhost:8090", "secret"
    )

    assert "<b>Acme</b>" not in email.html
    assert "&lt;b&gt;Acme&lt;/b&gt;" in email.html
    assert "<b>Acme</b> invited you" in email.text


def test_an_invite_event_sends_its_email(client, monkeypatch):
    sent = []

    async def fake_send(email):
        sent.append(email.to)

    monkeypatch.setattr(smtp, "send", fake_send)

    assert client.post("/internal/events", json=push("candidate.invited", DATA)).status_code == 204
    assert sent == ["bob@example.com"]


def test_resend_gets_the_message_id_so_a_retry_never_sends_twice(client, monkeypatch):
    sent = []

    async def fake_send(email, idempotency_key):
        sent.append((email.to, idempotency_key))

    monkeypatch.setattr(settings, "resend_api_key", "re_test")
    monkeypatch.setattr(resend, "send", fake_send)

    client.post("/internal/events", json=push("candidate.invited", DATA, "m-7"))
    client.post("/internal/events", json=push("candidate.invited", DATA, "m-7"))

    assert sent == [("bob@example.com", "events/m-7")] * 2


def test_an_event_re_sent_from_the_outbox_keeps_its_key(client, monkeypatch):
    sent = []

    async def fake_send(email, idempotency_key):
        sent.append(idempotency_key)

    monkeypatch.setattr(settings, "resend_api_key", "re_test")
    monkeypatch.setattr(resend, "send", fake_send)

    for message_id in ("m-8", "m-9"):
        body = push("candidate.invited", DATA, message_id)
        body["message"]["attributes"]["event_id"] = "row-1"
        client.post("/internal/events", json=body)

    assert sent == ["events/row-1"] * 2


def test_a_failed_send_answers_with_an_error_so_pubsub_retries(client, monkeypatch):
    async def failing_send(email):
        raise ConnectionError("SMTP is down")

    monkeypatch.setattr(smtp, "send", failing_send)

    with pytest.raises(ConnectionError):
        client.post("/internal/events", json=push("candidate.invited", DATA))


def test_other_events_are_accepted_without_an_email(client):
    response = client.post("/internal/events", json=push("answer.recorded", {}))

    assert response.status_code == 204


def resend_answering(monkeypatch, status_code):
    """Resend's API, answering every send with `status_code`."""
    transport = httpx.MockTransport(lambda request: httpx.Response(status_code, text="no"))
    monkeypatch.setattr(resend.http, "get_client", lambda: httpx.AsyncClient(transport=transport))


@pytest.mark.parametrize("status_code", [400, 422])
def test_an_address_resend_refuses_is_final(monkeypatch, status_code):
    resend_answering(monkeypatch, status_code)

    with pytest.raises(resend.EmailRefused):
        asyncio.run(
            resend.send(candidate_invite_email({**DATA, "company": "Acme"}, "", "secret"), "k")
        )


@pytest.mark.parametrize("status_code", [401, 409, 503])
def test_other_resend_errors_are_retried(monkeypatch, status_code):
    resend_answering(monkeypatch, status_code)

    with pytest.raises(RuntimeError):
        asyncio.run(
            resend.send(candidate_invite_email({**DATA, "company": "Acme"}, "", "secret"), "k")
        )


def test_over_resends_limit_pubsub_retries_without_a_server_error(client, monkeypatch):
    resend_answering(monkeypatch, 429)
    monkeypatch.setattr(settings, "resend_api_key", "re_test")

    response = client.post("/internal/events", json=push("candidate.invited", DATA))

    assert (response.status_code, response.headers["Retry-After"]) == (429, "1")


def test_a_refused_invite_is_marked_undelivered_and_not_retried(client, monkeypatch):
    reported = []

    async def refuse(email, key):
        raise resend.EmailRefused("422")

    async def undelivered(invite_id):
        reported.append(invite_id)

    monkeypatch.setattr(settings, "resend_api_key", "re_test")
    monkeypatch.setattr(resend, "send", refuse)
    monkeypatch.setattr(companies, "invite_undelivered", undelivered)
    data = {**DATA, "company": "Acme", "invite_id": "inv-1"}

    response = client.post("/internal/events", json=push("candidate.invited", data))

    assert response.status_code == 204
    assert reported == ["inv-1"]


def test_an_invite_is_emailed_in_the_interviews_language():
    data = {**DATA, "company": "Acme", "language": "ru"}
    email = candidate_invite_email(data, "http://localhost:8090", "secret")

    assert email.subject == EMAILS["ru"]["candidate"]["subject"].format(company="Acme")
    assert '<html lang="ru" dir="ltr">' in email.html
    assert "Или вставьте эту ссылку в браузер" in email.html
    assert "«Backend»" in email.text


def test_an_invite_in_a_language_without_texts_is_emailed_in_english():
    for language in ("xx", None):
        email = candidate_invite_email(
            {**DATA, "language": language}, "http://localhost:8090", "secret"
        )

        assert email.subject == EMAILS["en"]["candidate"]["subject"].format(company="Acme")
        assert '<html lang="en" dir="ltr">' in email.html


def test_an_arabic_invite_reads_right_to_left():
    data = {**DATA, "company": "Acme", "language": "ar"}
    email = candidate_invite_email(data, "http://localhost:8090", "secret")

    assert '<html lang="ar" dir="rtl">' in email.html
    assert 'dir="rtl"' in email.html.split("<body")[1]
    assert "text-align:right" in email.html
    assert email.subject == EMAILS["ar"]["candidate"]["subject"].format(company="Acme")


@pytest.mark.parametrize("language", sorted(LANGUAGES))
def test_every_content_language_has_the_invite_email(language):
    email = candidate_invite_email({**DATA, "language": language}, "", "secret")

    # Every placeholder is filled in, and the texts aren't English stand-ins.
    assert "{" not in email.html and "{" not in email.text
    assert f'lang="{language}"' in email.html
    assert language == "en" or email.subject != EMAILS["en"]["candidate"]["subject"].format(
        company="Acme"
    )


CONTACT = {
    "name": "<b>Ann</b>",
    "email": "ann@example.com",
    "message": "Hi\nthere",
    "language": "de",
}


def test_contact_email_goes_to_the_inbox_and_replies_to_the_visitor():
    email = contact_email(CONTACT, "hello@prepza.ai")

    assert email.to == "hello@prepza.ai"
    assert email.reply_to == "ann@example.com"
    assert email.subject == "Contact form: <b>Ann</b>"
    assert "From: <b>Ann</b> <ann@example.com>" in email.text
    assert "Hi\nthere" in email.text
    assert "<b>Ann</b>" not in email.html
    assert "&lt;b&gt;Ann&lt;/b&gt;" in email.html


def test_a_contact_event_sends_its_email(client, monkeypatch):
    sent = []

    async def fake_send(email):
        sent.append((email.to, email.reply_to))

    monkeypatch.setattr(smtp, "send", fake_send)

    assert client.post("/internal/events", json=push("contact.sent", CONTACT)).status_code == 204
    assert sent == [(settings.contact_email, "ann@example.com")]
