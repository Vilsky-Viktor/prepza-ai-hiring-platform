"""get_updates' checks per connection against the real database: kept, never moved back, and
gone with the daily retention once unused."""

import uuid
from datetime import UTC, datetime, timedelta

import httpx

from app.constants.updates import KEEP_DAYS
from app.main import app
from app.storage import update_checks


def test_a_connections_check_is_kept_and_never_moved_back(run):
    connection = f"grant-{uuid.uuid4().hex[:8]}"
    now = datetime.now(UTC)

    async def scenario():
        before = await update_checks.last(connection)
        await update_checks.save(connection, now)
        # A slower call that started earlier ends after it: it doesn't move the check back.
        await update_checks.save(connection, now - timedelta(minutes=1))
        kept = await update_checks.last(connection)
        await update_checks.save(connection, now + timedelta(minutes=1))

        return before, kept, await update_checks.last(connection)

    before, kept, later = run(scenario())

    assert (before, kept, later) == (None, now, now + timedelta(minutes=1))


def test_retention_drops_checks_unused_for_the_bells_keep_days(run):
    stale, recent = (f"key-{uuid.uuid4().hex[:8]}" for _ in range(2))
    now = datetime.now(UTC)

    async def scenario():
        await update_checks.save(stale, now - timedelta(days=KEEP_DAYS + 1))
        await update_checks.save(recent, now - timedelta(days=KEEP_DAYS - 1))
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(transport=transport, base_url="http://assistant") as api:
            response = await api.post("/internal/schedules/retention")

        return (
            response.status_code,
            await update_checks.last(stale),
            await update_checks.last(recent),
        )

    status, gone, kept = run(scenario())

    assert status == 204
    assert gone is None
    assert kept == now - timedelta(days=KEEP_DAYS - 1)
