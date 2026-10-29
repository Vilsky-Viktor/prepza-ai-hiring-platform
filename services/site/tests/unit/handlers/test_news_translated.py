"""Generation's `news.translated`: each translation is saved with the English it was made from,
so site drops a late one of an older text; an event that can never be saved (a translation past
the limits, no post id) is acknowledged and dropped, a failure a retry may fix answers 500."""

import uuid

import pytest
from event_pushes import failing_handler, push
from fastapi.testclient import TestClient
from prepza_common.config.constants import MAX_NEWS_TEXT_LENGTH

from site_content.api.v1 import events
from site_content.main import app
from site_content.repositories import news

POST_ID = uuid.uuid4()
EVENT = {
    "news_id": str(POST_ID),
    "title": "Practice in Thai",
    "text": "Line one.",
    "translations": {"de": {"title": "Üben auf Thai", "text": "Zeile eins."}},
}


@pytest.fixture
def saved(monkeypatch):
    calls = []

    async def save_translations(session, news_id, title, text, translations):
        calls.append(
            (news_id, title, text, {code: item.title for code, item in translations.items()})
        )

    monkeypatch.setattr(news, "save_translations", save_translations)

    return calls


def test_a_translation_is_saved_with_the_english_it_is_of(client, saved):
    response = client.post("/internal/events", json=push("news.translated", EVENT))

    assert response.status_code == 204
    assert saved == [(POST_ID, "Practice in Thai", "Line one.", {"de": "Üben auf Thai"})]


@pytest.mark.parametrize(
    "changes",
    [
        {"translations": {"de": {"title": "T", "text": "x" * (MAX_NEWS_TEXT_LENGTH + 1)}}},
        {"translations": {"xx": {"title": "T", "text": "X"}}},
        {"news_id": None},
    ],
)
def test_an_event_that_can_never_be_saved_is_acknowledged(client, saved, changes):
    response = client.post("/internal/events", json=push("news.translated", EVENT | changes))

    assert response.status_code == 204
    assert saved == []


def test_a_failure_a_retry_may_fix_is_answered_with_an_error(monkeypatch):
    failing_handler(monkeypatch, events, ConnectionError("The database went away"))
    client = TestClient(app, raise_server_exceptions=False)

    assert client.post("/internal/events", json=push("news.translated", EVENT)).status_code == 500
