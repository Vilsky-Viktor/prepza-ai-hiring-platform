import uuid
from datetime import UTC, datetime, timedelta

from app.helpers.unsubscribe import address_hash
from app.storage import soft_bounces


def test_soft_bounces_count_once_per_email_within_the_window_and_old_ones_are_forgotten(run):
    address = address_hash(f"b{uuid.uuid4().hex[:12]}@example.com")
    now = datetime.now(UTC)

    async def scenario():
        first = await soft_bounces.add(address, "e-1", now - timedelta(days=14))
        again = await soft_bounces.add(address, "e-1", now - timedelta(days=14))
        second = await soft_bounces.add(address, "e-2", now - timedelta(days=14))
        # A window starting after both: neither counts.
        later = await soft_bounces.add(address, "e-2", now + timedelta(minutes=1))
        await soft_bounces.forget(now + timedelta(minutes=1))
        gone = await soft_bounces.add(address, "e-3", now - timedelta(days=14))

        return first, again, second, later, gone

    assert run(scenario()) == (1, 1, 2, 0, 1)
