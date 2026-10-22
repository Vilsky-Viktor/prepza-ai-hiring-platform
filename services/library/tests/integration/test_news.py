from datetime import date

import httpx
from prepza_common.auth import current_user
from prepza_common.user import User
from sqlalchemy import select

from app.integrations import generation
from app.main import app
from app.models.outbox import OutboxEvent
from app.schemas.news import NewsIn, NewsTranslationIn
from app.storage import news
from app.storage.db import Session


def post(title, day, text="Text."):
    return NewsIn(title=title, text=text, published_on=day)


def every_language(title):
    return {
        code: NewsTranslationIn(title=f"{title} {code}", text=f"text {code}")
        for code in news.OTHER_LANGUAGES
    }


def test_posts_list_newest_first_a_page_at_a_time_in_the_readers_language(run):
    async def scenario():
        old = await news.create(post("Old", date(2026, 9, 1)))
        first = await news.create(post("First that day", date(2026, 10, 8)))
        second = await news.create(post("Second that day", date(2026, 10, 8)))
        await news.save_translations(
            first.id, first.title, first.text, {"de": NewsTranslationIn(title="Erster", text="T")}
        )
        german = await news.list_news("de", 0, 10)
        pages = [await news.list_news("en", offset, 2) for offset in (0, 2)]
        await news.remove(old.id)
        await news.remove(first.id)
        await news.remove(second.id)

        return german, pages

    german, pages = run(scenario())

    assert [title for _, title, _ in german] == ["Second that day", "Erster", "Old"]
    assert [[row[1] for row in page] for page in pages] == [
        ["Second that day", "First that day"],
        ["Old"],
    ]


def test_an_edit_drops_old_translations_and_late_ones_of_the_old_text(run):
    async def scenario():
        row = await news.create(post("Before", date(2026, 10, 8)))
        await news.save_translations(row.id, "Before", "Text.", every_language("Before"))
        complete = await news.untranslated()
        _, date_only = await news.update(row.id, post("Before", date(2026, 10, 9)))
        kept = await news.missing_languages(row.id)
        _, changed = await news.update(row.id, post("After", date(2026, 10, 9)))
        dropped = await news.missing_languages(row.id)
        # A job that translated the old text finishes after the edit: nothing is saved.
        await news.save_translations(row.id, "Before", "Text.", every_language("Before"))
        stale = await news.missing_languages(row.id)
        # Saved twice, the same translation replaces itself.
        for _ in range(2):
            await news.save_translations(row.id, "After", "Text.", every_language("After"))

        listed = await news.list_news("fr", 0, 10)
        await news.remove(row.id)
        await news.remove(row.id)
        gone = await news.get(row.id)

        return complete, date_only, kept, changed, dropped, stale, listed, gone, row.id

    complete, date_only, kept, changed, dropped, stale, listed, gone, row_id = run(scenario())

    assert row_id not in complete
    assert (date_only, kept) == (False, [])
    assert changed is True
    assert dropped == stale == news.OTHER_LANGUAGES
    assert [(title, text) for _, title, text in listed] == [("After fr", "text fr")]
    assert gone is None


def test_the_admin_tab_and_the_public_page_end_to_end(run, monkeypatch):
    """A superadmin writes a post through the routes; it's sent to be translated, the public
    page shows it in English until it is, and the tab shows when it's translated."""
    monkeypatch.setenv("SUPERADMIN_EMAILS", "sam@prepza.dev")
    sent = []

    async def translate_news(news_id):
        sent.append(news_id)

    monkeypatch.setattr(generation, "translate_news", translate_news)
    app.dependency_overrides[current_user] = lambda: User(
        uid="sam",
        email="sam@prepza.dev",
        email_verified=True,
        sign_in_provider="google.com",
    )
    body = {"title": "Hello", "text": "First line.\nSecond line.", "published_on": "2026-10-08"}

    async def scenario():
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(transport=transport, base_url="http://library") as client:
            created = (await client.post("/superadmin/news", json=body)).json()
            before = (await client.get("/news", headers={"Accept-Language": "ja"})).json()
            await news.save_translations(
                created["id"], "Hello", body["text"], every_language("Hello")
            )
            after = (await client.get("/news", headers={"Accept-Language": "ja"})).json()
            tab = (await client.get("/superadmin/news")).json()
            await client.delete(f"/superadmin/news/{created['id']}")
            empty = (await client.get("/news")).json()

        return created, before, after, tab, empty

    try:
        created, before, after, tab, empty = run(scenario())
    finally:
        app.dependency_overrides.clear()

    assert [str(item) for item in sent] == [created["id"]]
    assert created["translated"] is False
    assert [(row["title"], row["text"]) for row in before] == [("Hello", body["text"])]
    assert [row["title"] for row in after] == ["Hello ja"]
    assert [(row["id"], row["translated"]) for row in tab] == [(created["id"], True)]
    assert empty == []


def test_a_post_tells_everyones_bell_and_its_deletion_takes_the_notification_back(run):
    async def events_about(news_id):
        async with Session() as session:
            rows = await session.execute(
                select(OutboxEvent.event_type, OutboxEvent.data).where(
                    # The deletion names the post; the notification carries it in its data.
                    (OutboxEvent.data["news_id"].astext == str(news_id))
                    | (OutboxEvent.data["data"]["news_id"].astext == str(news_id))
                )
            )

            return sorted((event_type, data.get("recipient")) for event_type, data in rows)

    async def scenario():
        created = await news.create(post("In the bell", date(2026, 10, 16)))
        await news.save_translations(
            created.id,
            created.title,
            created.text,
            {"de": NewsTranslationIn(title="Im Glöckchen", text="T")},
        )
        titles = await news.titles([created.id], "de"), await news.titles([created.id], "fr")
        await news.remove(created.id)
        await news.remove(created.id)

        return titles, await events_about(created.id), await news.titles([created.id], "de")

    titles, events, gone = run(scenario())

    assert [list(found.values()) for found in titles] == [["Im Glöckchen"], ["In the bell"]]
    # Removed twice, announced once.
    assert events == [("news.deleted", None), ("notification.requested", "all")]
    assert gone == {}


def test_a_run_sends_a_batch_of_untranslated_posts_again_newest_first(run, monkeypatch):
    monkeypatch.setattr(news, "NEWS_RESEND_BATCH", 1)

    async def scenario():
        older = await news.create(post("Older", date(2026, 10, 8)))
        newer = await news.create(post("Newer", date(2026, 10, 9)))
        sent = await news.untranslated()
        await news.remove(older.id)
        await news.remove(newer.id)

        return sent, newer.id

    sent, newer_id = run(scenario())

    assert sent == [newer_id]
