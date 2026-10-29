"""Each action whose steps must succeed together is one save: when a later step fails, nothing
the earlier steps wrote is kept, so the retry (the caller's, or Pub/Sub's redelivery) finds the
whole action still to do."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from prepza_common.events.notifications import NotificationKind, Recipient, notification
from sqlalchemy import func, select

from notifications.constants.bulk import SEND_TAG
from notifications.constants.webhooks import COMPANY_TAG, ID_TAG, KIND_TAG
from notifications.helpers.unsubscribe import address_hash
from notifications.models.soft_bounces import SoftBounce
from notifications.repositories import (
    bulk_recipients,
    notifications,
    opt_outs,
    slack,
    soft_bounces,
    suppressed,
)
from notifications.services import accounts, notices, suppression, webhooks
from tests.integration.factories import company, finished
from tests.integration.transactions import transaction


async def broken(*args):
    raise RuntimeError("The database went away")


def address() -> str:
    return f"s{uuid.uuid4().hex[:12]}@example.com"


def test_an_account_deletion_whose_last_step_fails_keeps_the_users_notifications(run, monkeypatch):
    """The user's notifications, sent log, bulk rows and the Slack channels they made go
    together: a failure leaves everything for the event's redelivery."""
    user = f"u-{uuid.uuid4()}"
    monkeypatch.setattr(slack, "forget_maker", broken)

    async def scenario():
        own = notification(
            Recipient.USER, user, NotificationKind.REFERRAL_REWARDED, "/billing", title="Gift"
        )
        await notices.store(str(uuid.uuid4()), own)

        with pytest.raises(RuntimeError):
            await accounts.remove_user(user, "leaving@example.com")

        return await transaction(notifications.latest, [(Recipient.USER, user)], limit=None)

    assert len(run(scenario())) == 1


def test_a_company_deletion_whose_opt_outs_fail_keeps_its_notifications(run, monkeypatch):
    """A company's notifications and its candidates' opt-outs go together; until then the
    company still gets new ones, so the redelivered event finds it all to delete."""
    company_id = company()
    monkeypatch.setattr(opt_outs, "remove_company", broken)

    async def scenario():
        await notices.store(str(uuid.uuid4()), finished(company_id))

        with pytest.raises(RuntimeError):
            await accounts.remove_company(company_id)

        kept = await transaction(
            notifications.latest, [(Recipient.COMPANY, company_id)], limit=None
        )
        deleted = await transaction(notifications.is_deleted, f"{Recipient.COMPANY}:{company_id}")

        return len(kept), deleted

    assert run(scenario()) == (1, False)


def test_a_complaint_whose_campaign_count_fails_suppresses_nobody(run, monkeypatch):
    """The suppressed addresses and the complaint counted against its campaign go together."""
    to = address()
    monkeypatch.setattr(bulk_recipients, "mark_complained", broken)
    event = {
        "type": "email.complained",
        "data": {"to": [to], "tags": {SEND_TAG: str(uuid.uuid4()), ID_TAG: "u1"}},
    }

    async def scenario():
        with pytest.raises(RuntimeError):
            await suppression.from_webhook(event)

        return await transaction(suppressed.get, address_hash(to))

    assert run(scenario()) is None


def test_a_soft_bounce_whose_suppression_fails_isnt_counted(run, monkeypatch):
    """A temporary bounce is counted together with the suppression it brings: a failure counts
    nothing, so the web hook's retry counts it once."""
    to = address()
    since = datetime.now(UTC) - timedelta(days=1)
    monkeypatch.setattr(suppressed, "add", broken)

    async def scenario():
        for email_id in ("e-1", "e-2"):
            await transaction(soft_bounces.add, address_hash(to), email_id, since)

        with pytest.raises(RuntimeError):
            await suppression.soft_bounced({"to": [to], "email_id": "e-3"})

        return await transaction(bounces_of, address_hash(to))

    assert run(scenario()) == 2


async def bounces_of(session, hashed: str) -> int:
    return await session.scalar(
        select(func.count()).select_from(SoftBounce).where(SoftBounce.address == hashed)
    )


def test_a_reminders_complaint_stops_every_address_or_none(run, monkeypatch):
    """A complaint about a candidate's reminder stops that invite's reminders to each of its
    addresses in one save: a failure on the second keeps the first unstopped too."""
    company_id, invite_id = company(), str(uuid.uuid4())
    first, second = address(), address()
    add = opt_outs.add

    async def failing_second(session, hashed, *args):
        if hashed == address_hash(second):
            raise RuntimeError("The database went away")

        await add(session, hashed, *args)

    monkeypatch.setattr(opt_outs, "add", failing_second)
    tags = {KIND_TAG: "candidate_reminder", ID_TAG: invite_id, COMPANY_TAG: company_id}

    async def scenario():
        with pytest.raises(RuntimeError):
            await webhooks.complained(tags, [first, second])

        return await transaction(opt_outs.opted_out, address_hash(first), company_id, invite_id)

    assert run(scenario()) is False
