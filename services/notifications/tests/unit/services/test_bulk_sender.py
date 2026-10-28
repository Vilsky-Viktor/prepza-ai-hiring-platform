import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from prepza_common.limits.limit_list import LIMITS
from prepza_common.redis import memory_cache

from notifications.helpers.unsubscribe import address_hash
from notifications.integrations.resend import EmailRefused, ResendBusy
from notifications.repositories import bulk_recipients, bulk_sends, campaigns, suppressed
from notifications.services import bulk, delivery

SEND = "11111111-1111-1111-1111-111111111111"
CAMPAIGN = "22222222-2222-2222-2222-222222222222"
TEXTS = {"en": {"subject": "News", "text": "Hello.", "button": None}}


def person(user_id, updates=True):
    return {
        "user_id": user_id,
        "email": f"{user_id}@example.com",
        "language": "en",
        "preferences": {"updates": updates},
    }


@pytest.fixture
def store(monkeypatch):
    """Recipients' rows, people, suppressed addresses and delivery, in memory. `failing` maps a
    user to the error each try of theirs raises; `taken` rows are held by another run."""
    state = SimpleNamespace(
        rows={},
        kind="updates",
        about=CAMPAIGN,
        people={},
        suppressed=set(),
        sent=[],
        keys=[],
        failing={},
        taken=set(),
        sent_today=0,
    )

    def add(*user_ids):
        for user_id in user_ids:
            row_id = len(state.rows) + 1
            state.rows[row_id] = SimpleNamespace(
                id=row_id, user_id=user_id, status="pending", reason=None, attempts=0, sent_at=None
            )

    state.add = add

    async def pending(session, limit, skip):
        found = [
            (row.id, SEND, row.user_id, state.kind, state.about)
            for row in state.rows.values()
            if row.status == "pending" and row.id not in skip
        ]

        return found[:limit]

    async def still_pending(session, row_id):
        row = state.rows[row_id]

        if row_id in state.taken or row.status != "pending":
            return None

        # A copy, as a row read in a session that's closed again.
        return SimpleNamespace(**vars(row))

    async def save(session, row):
        vars(state.rows[row.id]).update(vars(row))

    async def recipients(ids):
        return [state.people[user_id] for user_id in ids if user_id in state.people]

    async def among(session, hashes):
        return {address for address in hashes if address in state.suppressed}

    async def transmit(email, key):
        user = email.to.split("@")[0]
        error = state.failing.get(user)

        if error is not None:
            raise error

        state.sent.append(email)
        state.keys.append(key)

    async def get_campaign(session, campaign_id):
        return SimpleNamespace(link=None), TEXTS

    async def nothing(*args):
        return []

    async def sent_since(session, since):
        return state.sent_today

    async def no_wait(_seconds):
        return None

    async def finish_done(session):
        return None

    monkeypatch.setattr(bulk_sends, "unprepared", nothing)
    monkeypatch.setattr(bulk_sends, "finish_done", finish_done)
    monkeypatch.setattr(bulk_recipients, "pending", pending)
    monkeypatch.setattr(bulk_recipients, "still_pending", still_pending)
    monkeypatch.setattr(bulk_recipients, "save", save)
    monkeypatch.setattr(bulk_recipients, "sent_since", sent_since)
    monkeypatch.setattr(bulk.accounts, "recipients", recipients)
    monkeypatch.setattr(suppressed, "among", among)
    monkeypatch.setattr(delivery, "transmit", transmit)
    monkeypatch.setattr(campaigns, "get", get_campaign)
    monkeypatch.setattr("notifications.services.bulk.asyncio.sleep", no_wait)

    return state


def run():
    """One run's sending, without the lock that keeps runs apart (tested on its own below)."""
    return asyncio.run(bulk.send_run(datetime.now(UTC)))


def statuses(store):
    return {row.user_id: (row.status, row.reason) for row in store.rows.values()}


def test_each_recipient_gets_one_email_with_its_own_key_and_a_rerun_sends_none(store):
    store.people = {name: person(name) for name in ("ann", "bob")}
    store.add("ann", "bob")

    assert run() == 2
    assert store.keys == [f"bulk/{SEND}/ann", f"bulk/{SEND}/bob"]
    assert {email.tags["send"] for email in store.sent} == {SEND}
    assert run() == 0


def test_a_row_another_run_holds_is_left_to_it(store):
    store.people = {name: person(name) for name in ("ann", "bob")}
    store.add("ann", "bob")
    store.taken = {1}

    assert run() == 1
    assert [email.to for email in store.sent] == ["bob@example.com"]
    assert statuses(store)["ann"] == ("pending", None)


def test_the_gone_the_suppressed_and_the_unsubscribed_are_skipped(store):
    store.people = {"bob": person("bob"), "cat": person("cat", updates=False), "dan": person("dan")}
    store.suppressed = {address_hash("bob@example.com")}
    store.add("ann", "bob", "cat", "dan")

    assert run() == 1
    assert statuses(store) == {
        "ann": ("skipped", "gone"),
        "bob": ("skipped", "suppressed"),
        "cat": ("skipped", "unsubscribed"),
        "dan": ("sent", None),
    }


def test_a_failure_is_tried_in_two_more_runs_then_failed_and_a_refusal_fails_at_once(store):
    store.people = {name: person(name) for name in ("ann", "bob")}
    store.failing = {"ann": RuntimeError("down"), "bob": EmailRefused("bad address")}
    store.add("ann", "bob")

    run()

    assert statuses(store)["ann"][0] == "pending"
    assert statuses(store)["bob"] == ("failed", "EmailRefused: bad address")

    run()
    run()

    assert statuses(store)["ann"] == ("failed", "RuntimeError: down")
    assert store.rows[1].attempts == 3


def test_resend_busy_stops_the_run_and_leaves_the_row_for_the_next(store):
    store.people = {name: person(name) for name in ("ann", "bob")}
    store.failing = {"ann": ResendBusy()}
    store.add("ann", "bob")

    with pytest.raises(ResendBusy):
        run()

    assert statuses(store)["ann"] == ("pending", None)
    assert store.rows[1].attempts == 0
    assert store.sent == []


class EditedLimits:
    """Redis holding the limits as the Controls tab edited them."""

    def __init__(self, values: dict):
        self.values = values

    async def hgetall(self, key):
        return {name.encode(): str(value).encode() for name, value in self.values.items()}


@pytest.mark.parametrize(("edited", "reserve"), [(None, None), (10, None), (100, 50)])
def test_the_days_share_of_resends_quota_keeps_room_for_invites(
    store, monkeypatch, published, edited, reserve
):
    """Resend's daily quota and the share kept from bulk sends as edited, or their defaults
    when they aren't."""
    quota = edited or LIMITS["RESEND_DAILY_LIMIT"].default
    kept = reserve if reserve is not None else LIMITS["RESEND_RESERVE_PERCENT"].default
    values = {"RESEND_DAILY_LIMIT": quota, "RESEND_RESERVE_PERCENT": kept}
    monkeypatch.setattr(memory_cache, "_entries", {})
    monkeypatch.setattr(bulk, "get_redis", lambda: EditedLimits(values))
    store.people = {name: person(name) for name in "abcdefghij"}
    store.add(*"abcdefghij")
    # The quota less the kept share (20% by default), less what was sent today, is left: 3.
    share = int(quota * (100 - kept) / 100)
    store.sent_today = share - 3

    assert run() == 3
    # The rest wait for tomorrow: the share is recorded as used up.
    assert [(data["limit"], data["what"]) for _, data in published] == [
        ("RESEND_DAILY_LIMIT", "bulk_email")
    ]

    store.sent_today = share

    assert run() == 0


def test_a_legal_notice_goes_whatever_the_settings(store):
    store.kind, store.about = "legal_terms", "2026-12-01"
    store.people = {"ann": person("ann", updates=False)}
    store.add("ann")

    assert run() == 1
    # The day it applies, as the recipient's language writes it.
    assert "December 1, 2026" in store.sent[0].subject


def test_a_campaign_deleted_while_sending_is_stopped_for_the_rest(store, monkeypatch):
    async def gone(session, campaign_id):
        return None

    monkeypatch.setattr(campaigns, "get", gone)
    store.people = {"ann": person("ann")}
    store.add("ann")

    assert run() == 0
    assert statuses(store) == {"ann": ("skipped", "stopped")}
    assert store.sent == []


def test_a_run_that_finds_another_still_going_sends_nothing(store, monkeypatch):
    class Held:
        async def set(self, key, value, nx, ex):
            return None

    store.people = {"a": person("a")}
    store.add("a")
    monkeypatch.setattr(bulk, "get_redis", lambda: Held())

    assert asyncio.run(bulk.send_bulk(datetime.now(UTC))) == 0
    assert statuses(store) == {"a": ("pending", None)}
