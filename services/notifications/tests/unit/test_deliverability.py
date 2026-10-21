import asyncio
import json
import re
from email.utils import parseaddr

import httpx
import pytest
from prepza_common.constants import LANGUAGES

from app.config.settings import settings
from app.constants.unsubscribe import UnsubscribeType
from app.helpers.campaign_emails import campaign_email
from app.helpers.emails import (
    candidate_invite_email,
    candidate_reminder_email,
    contact_email,
    render,
    report_email,
)
from app.helpers.member_emails import (
    digest_email,
    price_change_email,
    reminder_email,
    top_up_failed_email,
    top_up_paused_email,
)
from app.integrations import resend, smtp
from app.templates.emails import EMAILS

SITE = "https://prepza.ai"
SECRET = "test-email-link-secret"
INVITE = {
    "email": "bob@example.com",
    "token": "t",
    "title": "Backend",
    "company": "Acme",
    "company_id": "c1",
    "invite_id": "i1",
    "language": "en",
    # The day a legal notice's new version applies.
    "date": "2026-11-01",
}
RECIPIENT = {"user_id": "ann", "email": "ann@example.com", "language": "en"}
REPORT = {
    "email": "boss@example.com",
    "sender": "Bob",
    "reply_to": "bob@example.com",
    "company": "Acme",
    "title": "Backend",
    "candidate": "ann@example.com",
    "filename": "Report.pdf",
    "pdf": "JVBERi0=",
}
CONTACT = {"name": "Eve", "email": "eve@example.com", "language": "en", "message": "Hi"}
ROW = (
    f"{SITE}/companies/c1",
    {"title": "Backend", "company": "Acme", "ats": "Greenhouse", "count": 2},
)

# Every email the service sends, and whether it's one the recipient may stop with their mail
# client's unsubscribe button.
EMAILS_SENT = {
    "invite": (lambda: candidate_invite_email(INVITE, SITE, SECRET), False),
    "candidate reminder": (lambda: candidate_reminder_email(INVITE, SITE, SECRET), True),
    "report": (lambda: report_email(REPORT, SITE), False),
    "contact": (lambda: contact_email(CONTACT, "hello@prepza.ai"), False),
    "top-up failed": (lambda: top_up_failed_email(RECIPIENT, "Acme", SITE), False),
    "top-up paused": (lambda: top_up_paused_email(RECIPIENT, "Acme", f"{SITE}/b"), False),
    "top-up price change": (
        lambda: price_change_email(
            RECIPIENT,
            "Acme",
            {"price": 4500, "new_price": 5000, "currency": "USD", "date": "2026-11-21"},
            f"{SITE}/b",
        ),
        False,
    ),
    "digest": (
        lambda: digest_email(
            RECIPIENT, [("Acme", [("candidate_finished", ROW[1], ROW[0])])], SITE, SECRET
        ),
        True,
    ),
    "reminders": (
        lambda: reminder_email(
            "no_candidates", RECIPIENT, [("interview", ROW[1], ROW[0])], SITE, SECRET
        ),
        True,
    ),
    "campaign": (
        lambda: campaign_email(
            "updates",
            RECIPIENT,
            {"en": {"subject": "News", "text": "Hi.", "button": "See"}},
            "/news",
            SITE,
            SECRET,
            "s1",
        ),
        True,
    ),
}
OPTIONAL = {"digest", "reminders", "campaign"}


@pytest.mark.parametrize("name", EMAILS_SENT)
def test_every_email_is_marked_automated_and_only_optional_ones_can_be_unsubscribed(name):
    build, unsubscribable = EMAILS_SENT[name]
    email = build()

    assert email.headers["Auto-Submitted"] == "auto-generated"
    assert ("List-Unsubscribe" in email.headers) == unsubscribable
    assert ("List-Unsubscribe-Post" in email.headers) == unsubscribable
    # Only the digest and reminders go out on the optional emails' own address.
    assert email.optional == (name in OPTIONAL)
    assert email.text.strip()


def resend_payload(monkeypatch, email) -> dict:
    sent = {}

    def answer(request):
        sent.update(json.loads(request.content))

        return httpx.Response(200, json={"id": "e-1"})

    monkeypatch.setattr(
        resend.http, "get_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(answer))
    )
    monkeypatch.setattr(settings, "resend_api_key", "re_test")
    asyncio.run(resend.send(email, "k"))

    return sent


@pytest.mark.parametrize("name", EMAILS_SENT)
def test_resend_sends_each_stream_from_its_own_address_with_a_monitored_reply_to(monkeypatch, name):
    build, _ = EMAILS_SENT[name]
    email = build()
    sent = resend_payload(monkeypatch, email)
    sender = settings.mail_from_updates if name in OPTIONAL else settings.mail_from

    assert sent["from"] == sender
    assert sent["reply_to"] == (email.reply_to or settings.contact_email)
    assert sent["headers"] == email.headers
    assert sent["text"] == email.text


def test_the_optional_emails_address_differs_from_the_service_emails():
    assert settings.mail_from_updates != settings.mail_from


def test_smtp_sends_from_the_streams_address_with_a_date_and_a_message_id(monkeypatch):
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
    smtp.send_sync(EMAILS_SENT["digest"][0]())
    smtp.send_sync(EMAILS_SENT["invite"][0]())
    digest, invite = sent

    # Compared as addresses: SMTP quotes the display name ("prepza.").
    assert parseaddr(digest["From"]) == parseaddr(settings.mail_from_updates)
    assert parseaddr(invite["From"]) == parseaddr(settings.mail_from)
    assert invite["Reply-To"] == settings.contact_email
    assert invite["Auto-Submitted"] == "auto-generated"
    assert invite["List-Unsubscribe"] is None
    assert invite["Date"] and invite["Message-ID"]
    assert invite.get_body(("plain",)).get_content().strip()


def placeholders(language: str) -> dict:
    """Data for every placeholder any template uses."""
    return {
        **INVITE,
        "language": language,
        "sender": "Bob",
        "inviter": "Bob",
        "role": "admin",
        "candidate": "ann@example.com",
        "count": 2,
        "ats": "Greenhouse",
        "available": 5,
        "days": 3,
        # An automatic top-up's price and its new one, as the price notice writes them.
        "price": "$45",
        "new_price": "$50",
        # A campaign's own texts.
        "subject": "Code questions",
        "preheader": "Now with code.",
        "button": "See it",
    }


TEMPLATES = [kind for kind, texts in EMAILS["en"].items() if isinstance(texts, dict)]
FOOTER_LINKS = ["unsubscribe", "email_settings", "stop_reminders", "stop_company"]


@pytest.mark.parametrize("language", sorted(LANGUAGES))
@pytest.mark.parametrize("kind", TEMPLATES)
def test_every_email_in_every_language_has_a_full_text_part_and_links_only_to_the_site(
    kind, language
):
    texts = EMAILS[language][kind]
    data = placeholders(language)
    rows = [(row, data, f"{SITE}/companies/c1") for row in texts.get("rows", {})]
    links = [(key, f"{SITE}/unsubscribe?token=x") for key in FOOTER_LINKS]
    email = render(kind, data, f"{SITE}/invite/t", links, [("Acme", rows)] if rows else [])

    # The language has the email itself, not an English stand-in.
    assert texts["heading"].format(**data) in email.text
    assert f'lang="{language}"' in email.html
    # The text part says everything the HTML does: its lines, every link, and nothing unfilled.
    assert "{" not in email.text and "{" not in email.html
    assert f"{SITE}/invite/t" in email.text

    for _, url in links + [(row, url) for row, _, url in rows]:
        assert url in email.text

    # No tracking redirects or shorteners: every link and image is on the site.
    for url in re.findall(r'(?:href|src)="([^"]+)"', email.html):
        assert url.startswith(SITE), url

    # Gmail clips an email past 102 KB.
    assert len(email.html.encode()) < 100_000


def test_a_complaint_tag_names_the_optional_email_and_the_user():
    email = EMAILS_SENT["digest"][0]()

    assert email.tags == {"kind": UnsubscribeType.DIGEST, "id": "ann"}
