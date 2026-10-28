"""News posts and campaigns translated through OpenAI's Batch API (services/translation_jobs.py,
batch_work.py, batch_steps.py): one piece per missing language, sent in a batch, each reply
checked against the limits and saved, or asked for again. OpenAI and storage are fakes."""

import asyncio
import json
import uuid

import pytest
from prepza_common.ai.ai_constants import AI_USED
from prepza_common.config.constants import MAX_NEWS_TEXT_LENGTH

from generation.constants.actions import NEWS_TRANSLATION
from generation.constants.batch_work import BATCH_WORK_ATTEMPTS, BatchKind
from generation.integrations import library, notifications
from generation.schemas.campaigns import CampaignSource
from generation.schemas.news import NewsSource
from generation.services.translation_jobs import translate_campaign, translate_news
from tests.unit.batch_fakes import run_batches

NEWS_ID = uuid.uuid4()
CAMPAIGN_ID = uuid.uuid4()
POST = NewsSource(title="Practice in Thai", text="Line one.\nLine two.", missing=["de", "fr"])
CAMPAIGN = CampaignSource(subject="New", text="One.\n\nTwo.", button=None, missing=["de"])


def language_of(body: dict) -> str:
    return body["messages"][-1]["content"].rstrip(".").rsplit(" into ", 1)[1]


@pytest.fixture
def store(batch_store):
    return batch_store


@pytest.fixture
def saved(monkeypatch):
    calls = []

    async def news_source(news_id):
        return POST

    async def campaign_source(campaign_id):
        return CAMPAIGN

    async def save_news(news_id, source, translations):
        calls.append(("news", news_id, {k: v.model_dump() for k, v in translations.items()}))

    async def save_campaign(campaign_id, source, translations):
        calls.append(
            ("campaign", campaign_id, {k: v.model_dump() for k, v in translations.items()})
        )

    monkeypatch.setattr(library, "get_news_source", news_source)
    monkeypatch.setattr(library, "save_news_translations", save_news)
    monkeypatch.setattr(notifications, "get_campaign_source", campaign_source)
    monkeypatch.setattr(notifications, "save_campaign_translations", save_campaign)

    return calls


def test_each_missing_language_is_one_piece_queued_once(store, saved):
    asyncio.run(translate_news(NEWS_ID))
    asyncio.run(translate_news(NEWS_ID))

    rows = sorted(store.rows.values(), key=lambda row: row.key)
    assert [(row.kind, row.key) for row in rows] == [(BatchKind.NEWS, "de"), (BatchKind.NEWS, "fr")]
    body = rows[0].body
    # The role and rules first, the post as data and the language last; a strict schema.
    assert body["messages"][0]["role"] == "system"
    assert body["messages"][0]["content"].startswith("You are")
    assert "Line one.\nLine two." in body["messages"][1]["content"]
    assert language_of(body) == "German"
    assert body["response_format"]["json_schema"]["strict"] is True


def test_a_reply_within_the_limits_is_saved_and_priced_at_batch_price(
    store, saved, monkeypatch, events
):
    asyncio.run(translate_news(NEWS_ID))

    def answer(body):
        language = language_of(body)

        return json.dumps({"title": f" {language} title ", "text": f"{language} text"})

    run_batches(monkeypatch, answer)

    assert sorted(saved, key=lambda call: list(call[2])) == [
        ("news", NEWS_ID, {"de": {"title": "German title", "text": "German text"}}),
        ("news", NEWS_ID, {"fr": {"title": "French title", "text": "French text"}}),
    ]
    assert store.rows == {}
    used = [data for kind, data in events if kind == AI_USED]
    assert {data["action"] for data in used} == {NEWS_TRANSLATION}
    assert {data["subject_id"] for data in used} == {str(NEWS_ID)}


def test_a_reply_past_the_limits_is_asked_for_again_then_given_up(store, saved, monkeypatch):
    asyncio.run(translate_news(NEWS_ID))
    too_long = json.dumps({"title": "T", "text": "x" * (MAX_NEWS_TEXT_LENGTH + 1)})

    run_batches(monkeypatch, lambda body: too_long, rounds=BATCH_WORK_ATTEMPTS)

    assert saved == []
    assert store.rows == {}


def test_a_campaign_without_a_button_gets_none(store, saved, monkeypatch):
    asyncio.run(translate_campaign(CAMPAIGN_ID))
    reply = json.dumps({"subject": "Neu", "text": "Eins.\n\nZwei.", "button": "Erfunden"})

    run_batches(monkeypatch, lambda body: reply)

    assert saved == [
        (
            "campaign",
            CAMPAIGN_ID,
            {"de": {"subject": "Neu", "text": "Eins.\n\nZwei.", "button": ""}},
        )
    ]
