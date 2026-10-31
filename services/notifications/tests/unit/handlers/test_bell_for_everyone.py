import asyncio
import uuid
from datetime import UTC, datetime

import httpx
from testee_common.events.notifications import NEWS_WITHDRAWN

from notifications.handlers import dispatch
from notifications.repositories import notifications
from notifications.schemas.notifications import NotificationOut
from notifications.services import feed


def item(kind, **data):
    return NotificationOut(
        id=uuid.uuid4(), kind=kind, link="/news", data=data, created_at=datetime.now(UTC)
    )


def test_news_is_named_in_the_readers_language_and_a_deleted_post_left_out(monkeypatch):
    asked = []

    async def news_titles(ids, language):
        asked.append((ids, language))

        return {"n1": "Neu: Code-Fragen"}

    monkeypatch.setattr(feed.site, "news_titles", news_titles)
    items = [item("news", news_id="n1", title="New"), item("news", news_id="n2"), item("x")]

    shown = asyncio.run(feed.in_language(items, "de"))

    assert [(one.kind, one.data.get("title")) for one in shown] == [
        ("news", "Neu: Code-Fragen"),
        ("x", None),
    ]
    assert asked == [(["n1", "n2"], "de")]


def test_with_site_down_news_keeps_its_english_title(monkeypatch):
    async def news_titles(ids, language):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(feed.site, "news_titles", news_titles)
    items = [item("news", news_id="n1", title="New")]

    assert asyncio.run(feed.in_language(items, "de")) == items


def test_everyones_notifications_are_the_users_after_their_account_was_made(monkeypatch):
    made = datetime(2026, 10, 1, tzinfo=UTC)
    calls = []

    async def account_created(user_id):
        calls.append(user_id)

        return made

    monkeypatch.setattr(feed.accounts, "account_created", account_created)
    user = f"u-{uuid.uuid4()}"

    assert asyncio.run(feed.account_created(user)) == made
    assert asyncio.run(feed.account_created(user)) == made
    # Kept: it never changes.
    assert calls == [user]


def test_a_deleted_news_posts_notification_goes(monkeypatch):
    removed = []

    async def remove_news(session, news_id):
        removed.append(news_id)

    monkeypatch.setattr(notifications, "remove_news", remove_news)

    asyncio.run(dispatch.handle(NEWS_WITHDRAWN, {"news_id": "n1"}, "e1"))

    assert removed == ["n1"]
