import hashlib

import pytest
from event_pushes import push

from notifications.config import settings
from notifications.constants.unsubscribe import UnsubscribeType
from notifications.helpers.emails import candidate_reminder_email
from notifications.helpers.unsubscribe import address_hash, candidate_token, sign, user_token
from notifications.integrations import accounts, smtp
from notifications.repositories import bulk_recipients, opt_outs
from notifications.services import events

ANN = address_hash("ann@example.com")
INVITE = {
    "invite_id": "6f1c2c1e-0000-4000-8000-000000000001",
    "company_id": "c-1",
    "email": "ann@example.com",
    "token": "abc",
    "title": "Backend",
    "company": "Acme",
}


def token(kind: UnsubscribeType) -> str:
    if kind in (UnsubscribeType.COMPANY, UnsubscribeType.INVITE_REMINDERS):
        return candidate_token(INVITE, kind, settings.email_link_secret)

    return user_token("ann", kind, settings.email_link_secret)


@pytest.fixture
def applied(monkeypatch):
    """Library's settings and the opt-outs, recorded instead of stored."""
    calls = []

    async def unsubscribe(user_id, email_settings):
        calls.append(("library", user_id, email_settings))

    async def add(session, address, company_id, invite_id=None):
        calls.append(("opt_out", address, company_id, invite_id))

    async def mark_unsubscribed(session, user_id, kind):
        calls.append(("campaign", user_id, kind))

    monkeypatch.setattr(accounts, "unsubscribe", unsubscribe)
    monkeypatch.setattr(opt_outs, "add", add)
    monkeypatch.setattr(bulk_recipients, "mark_unsubscribed", mark_unsubscribed)

    return calls


def test_the_page_reads_what_a_link_stops_without_changing_anything(client, applied):
    company = client.get(f"/unsubscribe/{token(UnsubscribeType.COMPANY)}")
    digest = client.get(f"/unsubscribe/{token(UnsubscribeType.DIGEST)}")

    assert company.json() == {"type": "company", "company": "Acme"}
    assert digest.json() == {"type": "digest", "company": None}
    assert applied == []


def test_a_forged_link_is_not_found(client, applied):
    forged = token(UnsubscribeType.DIGEST)[:-3] + "abc"

    assert client.get(f"/unsubscribe/{forged}").status_code == 404
    assert client.post(f"/unsubscribe/{forged}").status_code == 404
    assert applied == []


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        (
            UnsubscribeType.DIGEST,
            (
                "library",
                "ann",
                ["candidate_finished", "invite_undelivered", "ats_not_invited", "interview_ready"],
            ),
        ),
        (UnsubscribeType.INTERVIEW_READY, ("library", "ann", ["interview_ready"])),
        (UnsubscribeType.PROMOTIONS, ("library", "ann", ["promotions"])),
        (UnsubscribeType.COMPANY, ("opt_out", ANN, "c-1", None)),
        (
            UnsubscribeType.INVITE_REMINDERS,
            ("opt_out", ANN, "c-1", INVITE["invite_id"]),
        ),
    ],
)
def test_confirming_applies_the_link(client, applied, kind, expected):
    assert client.post(f"/unsubscribe/{token(kind)}").status_code == 204
    # A campaign's setting is also counted against the campaign (tested below).
    assert [call for call in applied if call[0] != "campaign"] == [expected]


def test_a_link_sent_before_the_hashes_were_keyed_opts_out_the_same_address(client, applied):
    """Its token names the plain SHA-256; the opt-out keeps the keyed hash events look up."""
    plain = hashlib.sha256(b"ann@example.com").hexdigest()
    payload = {"type": "company", "address": plain, "company_id": "c-1", "company": "Acme"}
    old = sign(payload, settings.email_link_secret)

    assert client.post(f"/unsubscribe/{old}").status_code == 204
    assert applied == [("opt_out", ANN, "c-1", None)]


def test_a_mail_clients_one_click_post_applies_it_without_the_page(client, applied):
    response = client.post(
        f"/unsubscribe/{token(UnsubscribeType.UPDATES)}",
        content="List-Unsubscribe=One-Click",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 204
    assert applied == [("library", "ann", ["updates"]), ("campaign", "ann", "updates")]


@pytest.fixture
def outbox(monkeypatch):
    """What went out: emails sent, and invites reported undelivered; `opted` says who opted
    out, as (address hash, company, invite)."""
    record = {"sent": [], "undelivered": [], "opted": set()}

    async def send(email):
        record["sent"].append(email)

    async def report_undelivered(tags):
        record["undelivered"].append(tags["id"])

    async def opted_out(session, address, company_id, invite_id=None):
        return (address, company_id, None) in record["opted"] or (
            invite_id is not None and (address, company_id, invite_id) in record["opted"]
        )

    monkeypatch.setattr(smtp, "send", send)
    monkeypatch.setattr(events, "report_undelivered", report_undelivered)
    monkeypatch.setattr(opt_outs, "opted_out", opted_out)

    return record


def test_an_invite_to_someone_who_stopped_the_companys_emails_isnt_sent_and_shows_undelivered(
    client, outbox
):
    outbox["opted"].add((ANN, "c-1", None))

    assert (
        client.post("/internal/events", json=push("candidate.invited", INVITE)).status_code == 204
    )
    assert outbox["sent"] == []
    assert outbox["undelivered"] == [INVITE["invite_id"]]


def test_a_reminder_stopped_for_its_invite_isnt_sent_and_the_company_isnt_told(client, outbox):
    outbox["opted"].add((ANN, "c-1", INVITE["invite_id"]))

    client.post("/internal/events", json=push("candidate.reminded", INVITE))
    # The invite itself still goes, when the company sends it again.
    client.post("/internal/events", json=push("candidate.invited", INVITE))

    assert [email.tags["kind"] for email in outbox["sent"]] == ["candidate_invite"]
    assert outbox["undelivered"] == []


def test_a_reminder_to_someone_who_stopped_the_companys_emails_isnt_sent(client, outbox):
    outbox["opted"].add((ANN, "c-1", None))

    client.post("/internal/events", json=push("candidate.reminded", INVITE))

    assert outbox["sent"] == []


def test_smtp_sends_the_one_click_headers(monkeypatch):
    sent = []

    class Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def send_message(self, message):
            sent.append(message)

    monkeypatch.setattr(smtp.smtplib, "SMTP", Client)
    email = candidate_reminder_email(INVITE, "https://prepza.com", "secret")

    smtp.send_sync(email)

    assert sent[0]["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    assert sent[0]["List-Unsubscribe"].startswith("<https://prepza.com/api/notifications/")
