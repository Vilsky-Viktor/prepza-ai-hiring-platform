import uuid
from datetime import UTC, datetime, timedelta

from prepza_common.events.notifications import EVERYONE, NotificationKind, Recipient, notification

from app.integrations import companies, library
from app.services import feed
from app.storage import notifications


def test_everyones_news_reaches_users_older_than_it_is_seen_per_user_and_goes_with_the_post(run):
    news_id = str(uuid.uuid4())
    event = notification(
        Recipient.ALL, EVERYONE, NotificationKind.NEWS, f"/news#{news_id}", news_id=news_id
    )
    older, newer = f"u-{uuid.uuid4()}", f"u-{uuid.uuid4()}"
    before, after = datetime.now(UTC) - timedelta(days=1), datetime.now(UTC) + timedelta(days=1)

    def mine(user_id):
        return [(Recipient.USER, user_id)]

    async def news_of(user_id, since):
        items = await notifications.latest(mine(user_id), 100, since)

        return [item for item in items if item.data.get("news_id") == news_id]

    async def scenario():
        first = await notifications.add(f"news:{news_id}", event)
        again = await notifications.add(f"news:{news_id}", event)
        seen = (
            await news_of(older, before),
            await news_of(newer, after),
            await notifications.unread_count(mine(older), older, before),
        )
        await notifications.mark_seen(older)
        unread_after = await notifications.unread_count(mine(older), older, before)
        await notifications.remove_news(news_id)

        return first, again, seen, unread_after, await news_of(older, before)

    first, again, (old, new, unread), unread_after, gone = run(scenario())

    assert (first, again) == (True, False)
    assert len(old) == 1 and new == []
    assert unread >= 1 and unread_after == 0
    assert gone == []


def test_the_bell_names_the_news_in_the_readers_language_for_accounts_older_than_it(
    run, monkeypatch
):
    news_id = str(uuid.uuid4())
    event = notification(
        Recipient.ALL, EVERYONE, NotificationKind.NEWS, f"/news#{news_id}", news_id=news_id
    )
    older, newer = f"u-{uuid.uuid4()}", f"u-{uuid.uuid4()}"
    made = {
        older: datetime.now(UTC) - timedelta(days=1),
        newer: datetime.now(UTC) + timedelta(days=1),
    }

    async def company_ids(user_id):
        return []

    async def account_created(user_id):
        return made[user_id]

    async def news_titles(ids, language):
        return {news_id: f"Titel {language}"} if news_id in ids else {}

    monkeypatch.setattr(companies, "company_ids", company_ids)
    monkeypatch.setattr(library, "account_created", account_created)
    monkeypatch.setattr(library, "news_titles", news_titles)

    def news(found):
        return [
            (item.link, item.data["title"])
            for item in found.items
            if item.data.get("news_id") == news_id
        ]

    async def scenario():
        await notifications.add(f"news:{news_id}", event)
        seen = news(await feed.feed(older, "de")), news(await feed.feed(newer, "de"))
        await notifications.remove_news(news_id)

        return seen, news(await feed.feed(older, "de"))

    (old, new), gone = run(scenario())

    assert old == [(f"/news#{news_id}", "Titel de")]
    assert new == [] and gone == []
