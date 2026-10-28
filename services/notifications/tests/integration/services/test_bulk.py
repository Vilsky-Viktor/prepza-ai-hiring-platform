import asyncio
import uuid
from datetime import UTC, datetime

import pytest
from prepza_common.config.constants import GUEST_UID_PREFIX
from sqlalchemy import select

from notifications.core.db import Session
from notifications.models.bulk import BulkRecipient
from notifications.repositories import bulk_recipients, bulk_sends, campaigns
from notifications.services import audiences, bulk, delivery
from tests.integration.transactions import transaction

ENGLISH = {"subject": "Code questions", "text": "Now with code.", "button": None}


async def large_resend_quota(redis):
    """Resend's daily quota edited far above what the tests send, so emails other tests sent
    today never use up the bulk share."""
    return {"RESEND_DAILY_LIMIT": 1_000_000}


def people(*user_ids):
    return [
        {
            "user_id": user_id,
            "email": f"{user_id}@example.com",
            "language": "en",
            "preferences": {"updates": True},
        }
        for user_id in user_ids
    ]


@pytest.fixture
def sending(monkeypatch):
    """Library's answers and delivery, faked; every email sent is recorded by its key."""
    sent = []

    async def recipients(ids):
        return people(*ids)

    async def transmit(email, key):
        await asyncio.sleep(0)
        sent.append(key)

    async def no_wait(_seconds):
        return None

    monkeypatch.setattr(bulk.accounts, "recipients", recipients)
    monkeypatch.setattr(delivery, "transmit", transmit)
    monkeypatch.setattr("notifications.services.bulk.asyncio.sleep", no_wait)
    monkeypatch.setattr("prepza_common.limits.limits.current_values", large_resend_quota)

    return sent


def legal_send(user_ids):
    """A started legal notice, its recipients worked out; its id."""

    async def scenario():
        # A day far ahead, as a version is; each test starts with no sends.
        version = "2099-01-01"
        send_id = await transaction(bulk_sends.start, "legal_terms", version, "sam")
        first = await transaction(bulk_sends.save_page, send_id, "", user_ids[-1], user_ids, True)
        again = await transaction(
            bulk_sends.save_page, send_id, "", "late", [*user_ids, "late"], True
        )

        return send_id, first, again

    return scenario()


def test_recipients_are_worked_out_once_and_two_runs_at_once_send_each_one_email(run, sending):
    users = [f"u-{uuid.uuid4()}" for _ in range(6)]

    async def scenario():
        send_id, first, again = await legal_send(users)
        await asyncio.gather(bulk.send_bulk(datetime.now(UTC)), bulk.send_bulk(datetime.now(UTC)))
        counts = (await transaction(bulk_sends.counts, [send_id]))[send_id]

        return send_id, first, again, counts

    send_id, first, again, counts = run(scenario())
    mine = [key for key in sending if key.startswith(f"bulk/{send_id}/")]

    assert (first, again) == (True, False)
    assert sorted(mine) == sorted(f"bulk/{send_id}/{user}" for user in users)
    assert counts["sent"] == 6 and counts["pending"] == 0


@pytest.mark.parametrize("batch", [1000, 2])
def test_stopping_skips_the_rest_and_keeps_what_was_sent(run, sending, monkeypatch, batch):
    """Whether the rest fit in one batch or take several."""
    monkeypatch.setattr("prepza_common.db.db.DELETE_BATCH", batch)
    users = [f"u-{uuid.uuid4()}" for _ in range(3)]

    async def scenario():
        send_id, _, _ = await legal_send(users)
        await bulk.stop(send_id)
        await bulk.send_bulk(datetime.now(UTC))

        return send_id, (await transaction(bulk_sends.counts, [send_id]))[send_id]

    send_id, counts = run(scenario())

    assert not [key for key in sending if key.startswith(f"bulk/{send_id}/")]
    assert (counts["skipped"], counts["pending"]) == (3, 0)


def test_unsubscribes_count_against_the_last_campaign_and_a_deleted_account_leaves(run):
    user = f"u-{uuid.uuid4()}"

    async def scenario():
        send_id = await transaction(bulk_sends.start, "updates", str(uuid.uuid4()), "sam")
        await transaction(bulk_sends.save_page, send_id, "", user, [user], True)

        [row_id] = [
            row[0]
            for row in await transaction(bulk_recipients.pending, 10_000, [])
            if row[2] == user
        ]

        row = await transaction(bulk_recipients.still_pending, row_id)
        row.status, row.sent_at = "sent", datetime.now(UTC)
        await transaction(bulk_recipients.save, row)

        await transaction(bulk_recipients.mark_unsubscribed, user, "updates")
        await transaction(bulk_recipients.mark_complained, send_id, user)
        counts = (await transaction(bulk_sends.counts, [send_id]))[send_id]
        await transaction(bulk_recipients.remove_user, user)

        return counts, await transaction(bulk_recipients.is_recipient, send_id, user)

    counts, still = run(scenario())

    assert (counts["unsubscribed"], counts["complained"]) == (1, 1)
    assert still is False


class Crash(BaseException):
    """The instance dying halfway through a run: nothing in the sender catches it."""


def test_a_run_that_dies_halfway_leaves_the_rest_for_the_next_without_double_sends(
    run, sending, monkeypatch
):
    users = [f"u-{uuid.uuid4()}" for _ in range(4)]
    send_ids = []

    async def transmit(email, key):
        mine = [one for one in sending if one.startswith(f"bulk/{send_ids[0]}/")]

        if key.startswith(f"bulk/{send_ids[0]}/") and len(mine) == 2 and not crashed:
            crashed.append(key)

            raise Crash

        sending.append(key)

    crashed = []
    monkeypatch.setattr(delivery, "transmit", transmit)

    async def scenario():
        send_id, _, _ = await legal_send(users)
        send_ids.append(send_id)

        try:
            await bulk.send_bulk(datetime.now(UTC))
        except Crash:
            pass

        halfway = (await transaction(bulk_sends.counts, [send_id]))[send_id]
        await bulk.send_bulk(datetime.now(UTC))

        return halfway, (await transaction(bulk_sends.counts, [send_id]))[send_id]

    halfway, done = run(scenario())
    mine = [key for key in sending if key.startswith(f"bulk/{send_ids[0]}/")]

    assert (halfway["sent"], halfway["pending"]) == (2, 2)
    # The row being sent when it died stayed pending, and went once in the next run.
    assert crashed[0] in mine
    assert sorted(mine) == sorted(f"bulk/{send_ids[0]}/{user}" for user in users)
    assert (done["sent"], done["pending"]) == (4, 0)


def test_campaigns_sends_are_found_at_once_by_kind_and_what_they_are_about(run):
    about = str(uuid.uuid4())

    async def scenario():
        send_id = await transaction(bulk_sends.start, "updates", about, "sam")
        found = await transaction(
            bulk_sends.of_campaigns, [("updates", about), ("promotions", about)]
        )

        return send_id, {key: send.id for key, send in found.items()}

    send_id, found = run(scenario())

    assert found == {("updates", about): send_id}


@pytest.fixture
def audience(monkeypatch):
    """An audience of three users and a guest candidate, read two ids a page; the pages asked."""
    users = sorted([f"u-{uuid.uuid4()}" for _ in range(3)] + [f"{GUEST_UID_PREFIX}{uuid.uuid4()}"])
    asked = []

    async def user_ids(after, setting=None):
        asked.append(after)

        return [user for user in users if user > after][:2]

    monkeypatch.setattr("notifications.services.audiences.accounts.user_ids", user_ids)
    monkeypatch.setattr(audiences, "ID_PAGE_SIZE", 2)

    return users, asked


def campaign_send():
    """A started campaign send to everyone with product updates on, its recipients not worked
    out; (kind, about)."""

    async def scenario():
        everyone = {"kind": "updates", "groups": [], "editors_only": False, "company_ids": []}
        campaign = await transaction(campaigns.create, {**everyone, "link": None}, "sam", ENGLISH)
        await transaction(bulk_sends.start, "updates", str(campaign.id), "sam")

        return "updates", str(campaign.id)

    return scenario()


async def recipients_of(kind, about):
    """The send and the users saved as its recipients so far (sent only once it's prepared)."""
    send = await transaction(bulk_sends.get, kind, about)

    async with Session() as session:
        rows = await session.scalars(
            select(BulkRecipient.user_id).where(BulkRecipient.send_id == send.id)
        )

        return send, sorted(rows)


def test_an_audience_is_worked_out_a_page_a_run_each_going_on_where_the_last_stopped(run, audience):
    users, asked = audience

    async def scenario():
        kind, about = await campaign_send()
        pages = []

        # A run out of time works out one page; the next goes on after its last id.
        for _ in range(3):
            await bulk.prepare(await transaction(bulk_sends.get, kind, about), until=0)
            send, saved = await recipients_of(kind, about)
            pages.append((saved, send.prepared_at is not None))

        return pages

    pages = run(scenario())
    people = [user for user in users if not user.startswith(GUEST_UID_PREFIX)]

    assert [saved for saved, _ in pages] == [
        [user for user in users[:2] if user in people],
        people,
        people,
    ]
    assert [prepared for _, prepared in pages] == [False, False, True]
    assert asked == ["", users[1], users[3]]


def test_two_runs_working_out_one_audience_at_once_save_each_user_once(run, audience):
    users, _ = audience

    async def scenario():
        kind, about = await campaign_send()
        send = await transaction(bulk_sends.get, kind, about)
        await asyncio.gather(bulk.prepare(send, until=1e12), bulk.prepare(send, until=1e12))
        # Whichever stopped first, a later run finishes what's left.
        await bulk.prepare(await transaction(bulk_sends.get, kind, about), until=1e12)

        return await recipients_of(kind, about)

    send, saved = run(scenario())

    assert send.prepared_at is not None
    assert saved == [user for user in users if not user.startswith(GUEST_UID_PREFIX)]
