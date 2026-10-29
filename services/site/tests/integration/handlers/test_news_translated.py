"""Generation's `news.translated` through site's push route on a real database: delivered twice,
a translation is saved once; one of an older text, arriving after an edit, is dropped; one of a
deleted post saves nothing. Each test makes its own post and removes it."""

import uuid
from datetime import date

import httpx
from event_pushes import push

from site_content.integrations import generation
from site_content.main import app
from site_content.repositories import news
from site_content.schemas.news import NewsIn
from site_content.services import news as news_service
from tests.integration.transactions import transaction


def translated(news_id: uuid.UUID, title: str, language: str) -> dict:
    data = {
        "news_id": str(news_id),
        "title": title,
        "text": "Text.",
        "translations": {language: {"title": f"{title} {language}", "text": f"Text {language}."}},
    }

    return push("news.translated", data, f"e-{uuid.uuid4()}")


async def deliver(event: dict, times: int = 1) -> list[int]:
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://site") as client:
        return [
            (await client.post("/internal/events", json=event)).status_code for _ in range(times)
        ]


def test_a_translation_is_saved_once_and_a_late_one_of_an_older_text_is_dropped(run, monkeypatch):
    async def translate_news(news_id, source):
        return None

    monkeypatch.setattr(generation, "translate_news", translate_news)

    async def scenario():
        row = await transaction(
            news.create, NewsIn(title="Before", text="Text.", published_on=date(2026, 10, 8))
        )

        try:
            # Pub/Sub delivers the same event twice.
            statuses = await deliver(translated(row.id, "Before", "de"), times=2)
            saved = await transaction(news.list_news, "de", 0, 100)
            await news_service.update(
                row.id, NewsIn(title="After", text="Text.", published_on=date(2026, 10, 8))
            )
            # A translation of the old title, made before the edit, arrives after it.
            statuses += await deliver(translated(row.id, "Before", "fr"))
            missing = await transaction(news.missing_languages, row.id)
        finally:
            await transaction(news.remove, row.id)

        statuses += await deliver(translated(row.id, "After", "fr"))
        gone = await transaction(news.get, row.id)

        return row.id, statuses, saved, missing, gone

    row_id, statuses, saved, missing, gone = run(scenario())

    assert statuses == [204, 204, 204, 204]
    assert [(title, text) for post, title, text in saved if post.id == row_id] == [
        ("Before de", "Text de.")
    ]
    assert missing == news.OTHER_LANGUAGES
    assert gone is None
