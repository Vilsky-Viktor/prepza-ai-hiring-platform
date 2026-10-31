import asyncio
import logging
import time
from datetime import UTC, datetime

import pytest
from testee_common.events.notifications import NotificationKind, Recipient, notification

from notifications.constants.email import AUTOMATED_HEADERS
from notifications.constants.member_emails import CLEANUP_SECONDS
from notifications.integrations.resend import ResendBusy
from notifications.repositories import pending_notes, sent_emails, soft_bounces
from notifications.services import digest, events, member_sends, notices, reminders
from tests.unit.member_world import NOW, person


def test_the_digest_goes_to_every_member_once_a_day_for_the_hours_before_this_one(world):
    sent = asyncio.run(digest.send_digests(NOW))

    assert sent == 2
    assert sorted(email.to for email, _ in world["sent"]) == ["ann@example.com", "vic@example.com"]
    assert world["window"] == (
        datetime(2026, 10, 7, 7, tzinfo=UTC),
        datetime(2026, 10, 8, 7, tzinfo=UTC),
    )
    assert {claim[1:4] for claim in world["claims"]} == {("digest", NOW.date(), 1)}


def test_the_catch_up_hours_digest_covers_the_same_day_and_skips_who_got_it(world, monkeypatch):
    """Its window is the morning run's: a member the first hour missed gets the same digest."""
    claim = member_sends.claim

    async def once(user_id, kind, today, every_days, items):
        # Ann got hers in the first hour.
        if user_id == "ann":
            return None

        return await claim(user_id, kind, today, every_days, items)

    monkeypatch.setattr(member_sends, "claim", once)
    sent = asyncio.run(digest.send_digests(NOW.replace(hour=10, minute=5)))

    assert sent == 1
    assert [email.to for email, _ in world["sent"]] == ["vic@example.com"]
    assert world["window"] == (
        datetime(2026, 10, 7, 7, tzinfo=UTC),
        datetime(2026, 10, 8, 7, tzinfo=UTC),
    )


def test_no_digest_to_a_member_who_turned_its_kinds_off(world):
    world["people"] = [person("ann", candidate_finished=False), person("vic")]

    asyncio.run(digest.send_digests(NOW))

    assert [email.to for email, _ in world["sent"]] == ["vic@example.com"]


def test_reminders_go_to_owners_and_admins_who_get_them_once_a_week(world):
    sent = asyncio.run(reminders.send_reminders(NOW))

    assert sent == 2
    assert [(email.to, email.subject) for email, _ in world["sent"]] == [
        ("ann@example.com", "Your credits are running low"),
        ("ann@example.com", "Waiting for candidates"),
    ]
    # Credits again next week while low; each interview named once.
    assert [claim[1:] for claim in world["claims"]] == [
        ("low_credits", NOW.date(), 7, []),
        ("no_candidates", NOW.date(), 7, ["i1"]),
    ]


def test_no_reminders_to_someone_who_turned_them_off(world):
    world["people"] = [person("ann", reminders=False)]

    assert asyncio.run(reminders.send_reminders(NOW)) == 0
    assert world["claims"] == []


def test_a_send_over_resends_limit_is_taken_back_for_the_next_run(world):
    world["busy"] = True

    with pytest.raises(ResendBusy):
        asyncio.run(reminders.send_reminders(NOW))

    assert world["released"] == [("ann", "low_credits")]


@pytest.mark.parametrize("minute, level", [(30, logging.INFO), (59, logging.ERROR)])
def test_a_run_out_of_time_leaves_the_rest_to_the_next_unless_it_is_the_hours_last(
    world, monkeypatch, caplog, minute, level
):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW.replace(minute=minute)

    monkeypatch.setattr(member_sends, "datetime", Clock)
    jobs = [("ann", [], lambda new: pytest.fail("sent after the deadline"))]

    with caplog.at_level(logging.INFO):
        sent = asyncio.run(member_sends.send_once("digest", NOW.date(), 1, jobs, until=0))

    assert sent == 0
    assert [record.levelno for record in caplog.records] == [level]


def test_the_schedules_stop_quietly_when_resend_is_busy(client, world):
    world["busy"] = True

    assert client.post("/internal/schedules/digest").status_code == 204


def test_the_reminders_run_deletes_old_rows_only_until_its_cleanup_deadline(
    client, world, monkeypatch
):
    deadlines = []

    async def forget(sessions, before, until):
        deadlines.append(until)

    monkeypatch.setattr(sent_emails, "forget", forget)
    monkeypatch.setattr(soft_bounces, "forget", forget)
    monkeypatch.setattr(pending_notes, "forget", forget)
    started = time.monotonic()

    assert client.post("/internal/schedules/reminders").status_code == 204
    assert len(deadlines) == 3
    assert all(
        started + CLEANUP_SECONDS <= until <= time.monotonic() + CLEANUP_SECONDS
        for until in deadlines
    )


def test_a_failed_top_up_emails_the_companys_owners_and_admins_at_once(world, monkeypatch):
    async def stored(key, data):
        return True

    async def nothing(*args):
        return None

    monkeypatch.setattr(notices, "store", stored)
    monkeypatch.setattr(events, "announce", nothing)
    monkeypatch.setattr(events.slack, "deliver", nothing)
    event = notification(Recipient.COMPANY, "c1", NotificationKind.AUTO_TOP_UP_FAILED, "/top-up")

    asyncio.run(events.notify(event, "e-1"))
    asyncio.run(events.notify(event, "e-1"))

    # Viewers can't top up. A retry has the same key, so Resend sends it once.
    assert [(email.to, key) for email, key in world["sent"]] == [
        ("ann@example.com", "events/e-1/ann"),
        ("ann@example.com", "events/e-1/ann"),
    ]
    assert world["sent"][0][0].headers == AUTOMATED_HEADERS


def test_other_notifications_email_nobody(world, monkeypatch):
    async def stored(key, data):
        return True

    async def nothing(*args):
        return None

    monkeypatch.setattr(notices, "store", stored)
    monkeypatch.setattr(events, "announce", nothing)
    monkeypatch.setattr(events.slack, "deliver", nothing)
    event = notification(
        Recipient.COMPANY, "c1", NotificationKind.CANDIDATE_FINISHED, "/", title="x"
    )

    asyncio.run(events.notify(event, "e-2"))

    assert world["sent"] == []
