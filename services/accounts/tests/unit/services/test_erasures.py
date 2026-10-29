"""Accounts deleted in the backups' life are deleted again everywhere (companies by a call, the
others by `user.deleted`), so a restore brings nobody back (services/erasures.py)."""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import httpx
import pytest

from prepza_common.events.deletions import USER_DELETED

from accounts.integrations import services
from accounts.repositories import erasures, outbox, user_data
from accounts.services import erasures as replays
from accounts.services import outbox as outbox_service
from tests.unit.sessions import FakeSessions

NOW = datetime.now(UTC)


def erased(count: int) -> list:
    """Erasures, newest first, as pages read them."""
    return [
        SimpleNamespace(user_id=f"u{index}", email=f"u{index}@example.com", erased_at=NOW)
        for index in range(count)
    ]


class Calls(list):
    """The calls made, in order, and the erasures kept (`kept["rows"]`, newest first)."""

    kept: dict


@pytest.fixture
def done(monkeypatch):
    calls = Calls()
    kept = {"rows": erased(1)}

    async def page(session, after, below, size):
        calls.append(("page", after.tzinfo is not None, below))
        rows = kept["rows"]
        keys = [(row.erased_at, row.user_id) for row in rows]
        start = 0 if below is None else keys.index(below) + 1

        return rows[start : start + size]

    async def forget(session, before):
        calls.append("forget")

    async def delete_in_companies(user_id, email):
        calls.append(("companies", user_id, email))

    async def delete_own(session, user_id):
        calls.append(("own", user_id))

    async def record(session, user_id, email):
        calls.append(("erasure", user_id))

    async def flushed():
        calls.append("published")

    monkeypatch.setattr(erasures, "page", page)
    monkeypatch.setattr(erasures, "forget", forget)
    monkeypatch.setattr(erasures, "record", record)
    monkeypatch.setattr(services, "delete_in_companies", delete_in_companies)
    monkeypatch.setattr(user_data, "delete_user", delete_own)
    monkeypatch.setattr(
        outbox, "add", lambda session, kind, data: calls.append(("event", kind, data))
    )
    monkeypatch.setattr(outbox_service, "flush_quietly", flushed)
    monkeypatch.setattr(replays, "Session", FakeSessions())
    calls.kept = kept

    return calls


def test_every_recent_erasure_is_run_again_in_companies_and_by_event_after_older_ones_go(done):
    assert asyncio.run(replays.replay()) == 1

    assert done == [
        "forget",
        ("page", True, None),
        ("companies", "u0", "u0@example.com"),
        ("own", "u0"),
        # Kept from the first time (once per account).
        ("erasure", "u0"),
        # Every other holder deletes again what a restore brought back.
        ("event", USER_DELETED, {"user_id": "u0", "email": "u0@example.com"}),
        "published",
    ]


def test_erasures_are_read_a_batch_at_a_time_by_key(done, monkeypatch):
    monkeypatch.setattr(replays, "ERASURE_BATCH", 2)
    done.kept["rows"] = erased(3)

    assert asyncio.run(replays.replay()) == 3
    assert [call for call in done if call[0] == "page"] == [
        ("page", True, None),
        ("page", True, (NOW, "u1")),
    ]


def test_a_run_past_its_time_leaves_the_rest_to_the_next(done, monkeypatch):
    monkeypatch.setattr(replays, "ERASURE_BATCH", 2)
    monkeypatch.setattr(replays, "ERASURE_RUN_SECONDS", -1)
    done.kept["rows"] = erased(3)

    assert asyncio.run(replays.replay()) == 2
    assert ("own", "u2") not in done


def test_companies_refusing_a_shared_company_doesnt_stop_the_others(done, monkeypatch):
    async def refuse(user_id, email):
        response = httpx.Response(409, request=httpx.Request("DELETE", "http://companies"))
        raise httpx.HTTPStatusError("refused", request=response.request, response=response)

    monkeypatch.setattr(services, "delete_in_companies", refuse)

    assert asyncio.run(replays.replay()) == 1
    assert ("own", "u0") in done and "published" in done


def test_companies_failing_fails_the_run_to_be_retried(done, monkeypatch):
    async def down(user_id, email):
        raise httpx.ConnectError("companies is down")

    monkeypatch.setattr(services, "delete_in_companies", down)

    with pytest.raises(httpx.ConnectError):
        asyncio.run(replays.replay())

    assert ("own", "u0") not in done and "published" not in done
