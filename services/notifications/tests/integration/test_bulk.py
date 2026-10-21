import asyncio
import uuid
from datetime import UTC, datetime

import pytest

from app.services import bulk, delivery
from app.storage import bulk_recipients, bulk_sends


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

    monkeypatch.setattr(bulk.library, "recipients", recipients)
    monkeypatch.setattr(delivery, "transmit", transmit)
    monkeypatch.setattr("app.services.bulk.asyncio.sleep", no_wait)
    monkeypatch.setattr("prepza_common.limits.current_values", large_resend_quota)

    return sent


def legal_send(user_ids):
    """A started legal notice, its recipients worked out; its id."""

    async def scenario():
        version = f"2099-{uuid.uuid4().hex[:5]}"
        send_id = await bulk_sends.start("legal_terms", version, "sam")
        first = await bulk_sends.prepare(send_id, user_ids)
        again = await bulk_sends.prepare(send_id, [*user_ids, "late"])

        return send_id, first, again

    return scenario()


def test_recipients_are_worked_out_once_and_two_runs_at_once_send_each_one_email(run, sending):
    users = [f"u-{uuid.uuid4()}" for _ in range(6)]

    async def scenario():
        send_id, first, again = await legal_send(users)
        await asyncio.gather(bulk.send_bulk(datetime.now(UTC)), bulk.send_bulk(datetime.now(UTC)))
        counts = (await bulk_sends.counts([send_id]))[send_id]

        return send_id, first, again, counts

    send_id, first, again, counts = run(scenario())
    mine = [key for key in sending if key.startswith(f"bulk/{send_id}/")]

    assert (first, again) == (True, False)
    assert sorted(mine) == sorted(f"bulk/{send_id}/{user}" for user in users)
    assert counts["sent"] == 6 and counts["pending"] == 0


@pytest.mark.parametrize("batch", [1000, 2])
def test_stopping_skips_the_rest_and_keeps_what_was_sent(run, sending, monkeypatch, batch):
    """Whether the rest fit in one batch or take several."""
    monkeypatch.setattr(bulk_sends, "DELETE_BATCH", batch)
    users = [f"u-{uuid.uuid4()}" for _ in range(3)]

    async def scenario():
        send_id, _, _ = await legal_send(users)
        await bulk_sends.stop(send_id)
        await bulk.send_bulk(datetime.now(UTC))

        return send_id, (await bulk_sends.counts([send_id]))[send_id]

    send_id, counts = run(scenario())

    assert not [key for key in sending if key.startswith(f"bulk/{send_id}/")]
    assert (counts["skipped"], counts["pending"]) == (3, 0)


def test_unsubscribes_count_against_the_last_campaign_and_a_deleted_account_leaves(run):
    user = f"u-{uuid.uuid4()}"

    async def scenario():
        send_id = await bulk_sends.start("updates", str(uuid.uuid4()), "sam")
        await bulk_sends.prepare(send_id, [user])

        [row_id] = [row[0] for row in await bulk_recipients.pending(10_000, []) if row[2] == user]

        async with bulk_recipients.claimed(row_id) as row:
            row.status, row.sent_at = "sent", datetime.now(UTC)

        await bulk_recipients.mark_unsubscribed(user, "updates")
        await bulk_recipients.mark_complained(send_id, user)
        counts = (await bulk_sends.counts([send_id]))[send_id]
        await bulk_recipients.remove_user(user)

        return counts, await bulk_recipients.is_recipient(send_id, user)

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

        halfway = (await bulk_sends.counts([send_id]))[send_id]
        await bulk.send_bulk(datetime.now(UTC))

        return halfway, (await bulk_sends.counts([send_id]))[send_id]

    halfway, done = run(scenario())
    mine = [key for key in sending if key.startswith(f"bulk/{send_ids[0]}/")]

    assert (halfway["sent"], halfway["pending"]) == (2, 2)
    # The row being sent when it died stayed pending, and went once in the next run.
    assert crashed[0] in mine
    assert sorted(mine) == sorted(f"bulk/{send_ids[0]}/{user}" for user in users)
    assert (done["sent"], done["pending"]) == (4, 0)
