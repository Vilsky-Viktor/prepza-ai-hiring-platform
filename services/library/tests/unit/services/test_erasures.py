"""Accounts deleted in the backups' life are deleted again everywhere, so a restore brings
nobody back (services/erasures.py)."""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import httpx
import pytest

from library.integrations import accounts as services
from library.repositories import accounts, erasures
from library.services import erasures as replays

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

    async def page(after, below, size):
        calls.append(("page", after.tzinfo is not None, below))
        rows = kept["rows"]
        keys = [(row.erased_at, row.user_id) for row in rows]
        start = 0 if below is None else keys.index(below) + 1

        return rows[start : start + size]

    async def forget(before):
        calls.append("forget")

    async def delete_user(service, user_id, email):
        calls.append((service, user_id, email))

    async def delete_library(user_id):
        calls.append(("library", user_id))

    monkeypatch.setattr(erasures, "page", page)
    monkeypatch.setattr(erasures, "forget", forget)
    monkeypatch.setattr(services, "delete_user", delete_user)
    monkeypatch.setattr(accounts, "delete_user", delete_library)
    calls.kept = kept

    return calls


def test_every_recent_erasure_is_run_again_in_every_service_after_older_ones_go(done):
    assert asyncio.run(replays.replay()) == 1

    assert done[:2] == ["forget", ("page", True, None)]
    assert sorted(done[2:-1]) == sorted(
        (service, "u0", "u0@example.com") for service in services.services()
    )
    assert done[-1] == ("library", "u0")


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
    assert ("library", "u2") not in done


def test_a_service_refusing_a_shared_company_doesnt_stop_the_others(done, monkeypatch):
    async def refuse(service, user_id, email):
        if service == "companies":
            response = httpx.Response(409, request=httpx.Request("DELETE", "http://companies"))
            raise httpx.HTTPStatusError("refused", request=response.request, response=response)

        done.append(service)

    monkeypatch.setattr(services, "delete_user", refuse)

    assert asyncio.run(replays.replay()) == 1
    assert "rounds" in done and ("library", "u0") in done


def test_a_service_failing_fails_the_run_to_be_retried(done, monkeypatch):
    async def down(service, user_id, email):
        if service == "rounds":
            raise httpx.ConnectError("rounds is down")

    monkeypatch.setattr(services, "delete_user", down)

    with pytest.raises(httpx.ConnectError):
        asyncio.run(replays.replay())

    assert ("library", "u0") not in done
