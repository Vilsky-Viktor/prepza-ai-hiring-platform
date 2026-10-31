"""The daily reconciliation with Paddle: what its web hooks missed is handled, what they did is
skipped, and reading Paddle's lists pages through them within bounds."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from testee_common.http import http

from billing.constants.reconciliation import RECONCILE_MAX_PAGES, RECONCILE_WINDOW
from billing.integrations import paddle
from billing.repositories import purchases
from billing.services import reconciliation

NOW = datetime(2026, 10, 21, 5, tzinfo=UTC)


@pytest.fixture
def world(monkeypatch):
    """Paddle's records and billing's, faked: `credited` transactions and `counted` adjustments
    are already done; handling one does it."""
    state = {"transactions": [], "adjustments": [], "credited": set(), "counted": set()}
    handled = []

    async def completed_transactions(since):
        state["since"] = since

        return state["transactions"]

    async def approved_adjustments(since):
        return state["adjustments"]

    async def credited(session, ids):
        return {id_ for id_ in ids if id_ in state["credited"]}

    async def counted(session, pairs):
        return {adjustment for _, adjustment in pairs if adjustment in state["counted"]}

    async def handle_completed(data):
        handled.append(data["id"])

        if data["id"] == "txn_broken":
            raise RuntimeError("broken")

        state["credited"].add(data["id"])

    async def handle_adjustment(data):
        handled.append(data["id"])
        state["counted"].add(data["id"])

    monkeypatch.setattr(paddle, "completed_transactions", completed_transactions)
    monkeypatch.setattr(paddle, "approved_adjustments", approved_adjustments)
    monkeypatch.setattr(purchases, "credited", credited)
    monkeypatch.setattr(purchases, "counted", counted)
    monkeypatch.setattr(reconciliation, "handle_completed", handle_completed)
    monkeypatch.setattr(reconciliation, "handle_adjustment", handle_adjustment)

    return state, handled


def test_what_the_web_hooks_missed_is_handled_and_logged(world, caplog):
    state, handled = world
    state["transactions"] = [{"id": "txn_done"}, {"id": "txn_missed"}]
    state["credited"] = {"txn_done"}
    state["adjustments"] = [
        {"id": "adj_done", "transaction_id": "txn_done"},
        {"id": "adj_missed", "transaction_id": "txn_missed"},
    ]
    state["counted"] = {"adj_done"}

    with caplog.at_level(logging.WARNING):
        asyncio.run(reconciliation.reconcile(NOW))

    # Payments first, then their refunds.
    assert handled == ["txn_missed", "adj_missed"]
    assert state["since"] == NOW - RECONCILE_WINDOW
    assert "credited transaction txn_missed" in caplog.text
    assert "counted adjustment adj_missed" in caplog.text
    assert "txn_done" not in caplog.text


def test_one_failing_transaction_leaves_the_rest_handled(world, caplog):
    state, handled = world
    state["transactions"] = [{"id": "txn_broken"}, {"id": "txn_missed"}]

    with caplog.at_level(logging.ERROR):
        asyncio.run(reconciliation.reconcile(NOW))

    assert handled == ["txn_broken", "txn_missed"]
    assert "Reconciling txn_broken failed" in caplog.text


def test_a_second_run_changes_nothing(world):
    state, handled = world
    state["transactions"] = [{"id": "txn_missed"}]
    state["adjustments"] = [{"id": "adj_missed", "transaction_id": "txn_missed"}]

    asyncio.run(reconciliation.reconcile(NOW))
    asyncio.run(reconciliation.reconcile(NOW))

    assert handled == ["txn_missed", "adj_missed"]


def pages_of(items: list[dict], size: int, seen: list):
    """Paddle's list endpoint over `items`, `size` a page, after the id it's given."""

    def answer(request: httpx.Request) -> httpx.Response:
        seen.append(dict(request.url.params))
        after = request.url.params.get("after")
        start = next(i + 1 for i, item in enumerate(items) if item["id"] == after) if after else 0
        page = items[start : start + size]
        more = start + size < len(items)

        return httpx.Response(200, json={"data": page, "meta": {"pagination": {"has_more": more}}})

    return answer


def use(monkeypatch, handler) -> None:
    monkeypatch.setattr(
        http, "get_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )


def test_transactions_are_read_page_after_page_since_the_time_given(monkeypatch):
    items = [{"id": f"txn_{i}"} for i in range(5)]
    seen = []
    use(monkeypatch, pages_of(items, 2, seen))

    found = asyncio.run(paddle.completed_transactions(NOW - timedelta(days=7)))

    assert [item["id"] for item in found] == [item["id"] for item in items]
    assert seen[0]["status"] == "completed"
    assert seen[0]["updated_at[GTE]"] == "2026-10-14T05:00:00Z"
    assert [page.get("after") for page in seen] == [None, "txn_1", "txn_3"]


def test_adjustments_stop_at_the_first_older_than_the_window(monkeypatch):
    since = NOW - timedelta(days=7)
    items = [
        {"id": "adj_3", "created_at": "2026-10-20T00:00:00Z"},
        {"id": "adj_2", "created_at": "2026-10-15T00:00:00Z"},
        {"id": "adj_1", "created_at": "2026-10-01T00:00:00Z"},
        {"id": "adj_0", "created_at": "2026-09-01T00:00:00Z"},
    ]
    seen = []
    use(monkeypatch, pages_of(items, 2, seen))

    found = asyncio.run(paddle.approved_adjustments(since))

    assert [item["id"] for item in found] == ["adj_3", "adj_2"]
    assert seen[0]["status"] == "approved"
    assert len(seen) == 2


def test_reading_stops_after_the_most_pages_a_run_reads(monkeypatch, caplog):
    items = [{"id": f"txn_{i}"} for i in range(RECONCILE_MAX_PAGES + 5)]
    seen = []
    use(monkeypatch, pages_of(items, 1, seen))

    with caplog.at_level(logging.WARNING):
        found = asyncio.run(paddle.completed_transactions(NOW))

    assert len(found) == len(seen) == RECONCILE_MAX_PAGES
    assert "the rest waits" in caplog.text
