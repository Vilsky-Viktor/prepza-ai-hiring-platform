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
        kept = [item.user_id for item in await erasures.page(hour_ago, None, 1000)]
        await erasures.forget(datetime.now(UTC) + timedelta(seconds=1))

        return kept, [item.user_id for item in await erasures.page(hour_ago, None, 1000)]

    kept, after = run(scenario())

    assert kept.count(user_id) == 1
    assert user_id not in after


def test_erasures_are_read_newest_first_a_page_at_a_time(run):
    marker = uuid.uuid4()
    users = [f"gone-{marker}-{index}" for index in range(3)]

    async def scenario():
        for user_id in users:
            await erasures.record(user_id, "gone@example.com")

        hour_ago = datetime.now(UTC) - timedelta(hours=1)
        pages, below = [], None

        while True:
            page = await erasures.page(hour_ago, below, 2)
            pages.append([item.user_id for item in page])

            if len(page) < 2:
                return pages

            below = (page[-1].erased_at, page[-1].user_id)

    pages = run(scenario())
    seen = [user_id for page in pages for user_id in page]

    # Other tests' erasures may be among them: ours come once each, the latest first.
    assert [user_id for user_id in seen if user_id in users] == users[::-1]
    assert all(len(page) <= 2 for page in pages)
