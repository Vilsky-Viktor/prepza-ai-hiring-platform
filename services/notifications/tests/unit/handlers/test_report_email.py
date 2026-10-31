import asyncio
import base64
import json

import httpx

from notifications.config import settings
from notifications.helpers.emails import (
    candidate_invite_email,
    candidate_reminder_email,
    report_email,
)
from notifications.integrations import resend, smtp

PDF = base64.b64encode(b"%PDF-1.3 a report").decode()
DATA = {
    "email": "boss@example.com",
    "sender": "Bob",
    "reply_to": "bob@example.com",
    "company": "Arcolabs",
    "title": "Backend",
    "candidate": "ann@example.com",
    "language": "en",
    "pdf": PDF,
}


def test_the_report_email_carries_the_pdf_and_replies_go_to_the_sender():
    email = report_email(DATA, "https://testee.com")

    assert email.to == "boss@example.com"
    assert "ann@example.com" in email.subject
    assert email.reply_to == "bob@example.com"
    assert email.attachments == [("Candidate report – ann@example.com.pdf", PDF)]
    # The PDF travels as an attachment only; its own reason for being sent is in the footer.
    assert PDF not in email.html and PDF not in email.text
    assert "Bob shared a candidate report with this address" in email.text


def test_the_report_of_all_candidates_has_its_own_text():
    data = {key: value for key, value in DATA.items() if key != "candidate"}
    data |= {"kind": "candidates", "language": "en"}

    email = report_email(data, "https://testee.com")

    assert "Backend" in email.subject
    assert email.attachments == [("Candidates report – Backend.pdf", PDF)]
    assert "Bob shared a candidates report with this address" in email.text


def test_resend_gets_the_attachment(monkeypatch):
    sent = {}

    def answer(request):
        sent.update(json.loads(request.content))

        return httpx.Response(200, json={"id": "e-1"})

    monkeypatch.setattr(
        resend.http,
        "get_client",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(answer)),
    )
    monkeypatch.setattr(settings, "resend_api_key", "re_test")

    asyncio.run(resend.send(report_email(DATA, ""), "k"))

    assert sent["attachments"] == [
        {"filename": "Candidate report – ann@example.com.pdf", "content": PDF}
    ]
    assert sent["reply_to"] == "bob@example.com"


def test_smtp_attaches_the_pdf(monkeypatch):
    sent = []

    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def send_message(self, message):
            sent.append(message)

    monkeypatch.setattr(smtp.smtplib, "SMTP", FakeSMTP)

    smtp.send_sync(report_email(DATA, ""))

    [attachment] = list(sent[0].iter_attachments())
    assert attachment.get_filename() == "Candidate report – ann@example.com.pdf"
    assert attachment.get_content() == b"%PDF-1.3 a report"


def test_a_reminder_opens_the_same_invite_and_is_tagged_with_it():
    data = {
        "invite_id": "i-1",
        "email": "ann@example.com",
        "token": "abc",
        "title": "Backend",
        "company": "Acme",
        "language": "en",
    }

    reminder = candidate_reminder_email(data, "https://testee.com", "secret")

    assert "Acme" in reminder.subject
    assert "https://testee.com/invite/abc" in reminder.text
    assert reminder.tags == {"kind": "candidate_reminder", "id": "i-1"}


def test_an_invite_from_a_company_with_a_logo_shows_it_beside_the_title():
    data = {
        "invite_id": "i-1",
        "email": "ann@example.com",
        "token": "abc",
        "title": "Backend",
        "company": "Acme & Co",
        "language": "en",
        "logo_path": "/api/companies/companies/c-1/logo?v=2",
    }

    with_logo = candidate_invite_email(data, "https://testee.com/", "secret")
    without = candidate_invite_email({**data, "logo_path": None}, "https://testee.com/", "secret")

    assert (
        '<img src="https://testee.com/api/companies/companies/c-1/logo?v=2" alt="Acme &amp; Co"'
        in with_logo.html
    )
    assert "<img" not in without.html
    # Beside the title, at its end: in the title's row, after it, with the gap on the title's side.
    title_row = with_logo.html.split("</h1></td>", 1)[1].split("</tr>", 1)[0]
    assert 'height="80"' in title_row
    assert "padding:0 0 0 16px;" in title_row

    rtl = candidate_invite_email({**data, "language": "ar"}, "https://testee.com/", "secret")

    assert "padding:0 16px 0 0;" in rtl.html


def test_an_attachment_is_named_in_the_emails_language_without_unsafe_characters():
    data = DATA | {"language": "de", "candidate": 'Ann "A/B" Lee (ann@example.com)'}

    [(name, _)] = report_email(data, "https://testee.com").attachments

    assert name.endswith(".pdf")
    assert not any(char in name for char in '/\\:*?"<>|')
    assert "Ann A B Lee" in name
    assert not name.startswith("Candidate report")


def test_a_reminder_from_a_company_carries_its_id_for_a_complaint():
    data = {
        "invite_id": "i-1",
        "company_id": "c-1",
        "email": "ann@example.com",
        "token": "abc",
        "title": "Backend",
        "company": "Acme",
    }

    tags = candidate_reminder_email(data, "https://testee.com", "secret").tags

    assert tags == {"kind": "candidate_reminder", "id": "i-1", "company": "c-1"}
