"""The deleted accounts kept for a restore: once per account, and forgotten after their time."""

import uuid
from datetime import UTC, datetime, timedelta

from app.storage import erasures


def test_an_erasure_is_kept_once_and_forgotten_after_its_time(run):
    user_id = f"gone-{uuid.uuid4()}"

    async def scenario():
        await erasures.record(user_id, "gone@example.com")
        await erasures.record(user_id, "gone@example.com")
        hour_ago = datetime.now(UTC) - timedelta(hours=1)
        kept = [item.user_id for item in await erasures.since(hour_ago)]
        await erasures.forget(datetime.now(UTC) + timedelta(seconds=1))

        return kept, [item.user_id for item in await erasures.since(hour_ago)]

    kept, after = run(scenario())

    assert kept.count(user_id) == 1
    assert user_id not in after
