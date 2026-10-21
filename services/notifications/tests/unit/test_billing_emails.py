"""An automatic top-up that failed, paused or will cost a new price is emailed to the company's
owners and admins, whatever their email settings; nothing else is, and nobody else gets it."""

import asyncio

import pytest
from prepza_common.notifications import notification

from app.config.settings import settings
from app.integrations import companies, library
from app.services import delivery, service_emails

COMPANY = {
    "id": "c1",
    "name": "Acme",
    "members": [{"user_id": "ann", "editor": True}, {"user_id": "vic", "editor": False}],
}
NOTICE = {"price": 4500, "new_price": 5000, "currency": "USD", "date": "2026-11-21"}


@pytest.fixture
def sent(monkeypatch):
    """What was sent, by key; the recipients asked for."""
    found = {"sent": [], "asked": []}

    async def members(company_ids):
        return [COMPANY]

    async def recipients(user_ids):
        found["asked"].append(user_ids)

        return [
            {"user_id": uid, "email": f"{uid}@example.com", "language": "en"} for uid in user_ids
        ]

    async def send(email, key):
        found["sent"].append((key, email.subject, email.text))

    monkeypatch.setattr(companies, "members", members)
    monkeypatch.setattr(library, "recipients", recipients)
    monkeypatch.setattr(delivery, "send", send)
    monkeypatch.setattr(settings, "site_url", "https://prepza.ai")

    return found


@pytest.mark.parametrize(
    ("kind", "data", "opens"),
    [
        ("auto_top_up_failed", {}, "https://prepza.ai/top-up"),
        ("auto_top_up_paused", {}, "https://prepza.ai/companies/c1/billing"),
        ("auto_top_up_price_change", NOTICE, "https://prepza.ai/companies/c1/billing"),
    ],
)
def test_each_billing_notice_is_emailed_once_to_each_owner_and_admin(sent, kind, data, opens):
    event = notification("company", "c1", kind, "/companies/c1/billing", **data)

    asyncio.run(service_emails.billing_emails(event, "k1"))

    assert sent["asked"] == [["ann"]]
    [(key, subject, text)] = sent["sent"]
    assert key == "events/k1/ann"
    assert "Acme" in subject
    assert opens in text


@pytest.mark.parametrize(
    "event",
    [
        notification("company", "c1", "auto_top_up_charged", "/top-up", credits=5000),
        notification("user", "ann", "auto_top_up_paused", "/companies/c1/billing"),
    ],
)
def test_other_notices_and_a_persons_own_arent_emailed(sent, event):
    asyncio.run(service_emails.billing_emails(event, "k1"))

    assert sent == {"sent": [], "asked": []}
