"""News posts and campaigns translated through OpenAI's Batch API (services/translation_jobs.py,
batch_work.py, batch_steps.py): one piece per missing language, sent in a batch, each reply
checked against the limits and sent back as an event (a post's to site, a campaign's to
notifications), or asked for again. OpenAI and storage are fakes."""

import asyncio
import json
import uuid

import pytest
from testee_common.ai.ai_constants import AI_USED
from testee_common.config.constants import MAX_NEWS_TEXT_LENGTH
from testee_common.events.campaigns import CAMPAIGN_TRANSLATED, CampaignTranslated
from testee_common.events.news import NEWS_TRANSLATED, NewsTranslated

from generation.constants.actions import NEWS_TRANSLATION
from generation.constants.batch_work import BATCH_WORK_ATTEMPTS, BatchKind
from generation.schemas.campaigns import CampaignSource
from generation.schemas.news import NewsSource
from generation.services import batch_work
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

    async def flushed():
        calls.append("published")

    monkeypatch.setattr(batch_work.outbox, "add", lambda session, event: calls.append(event))
    monkeypatch.setattr(batch_work.outbox_service, "flush_quietly", flushed)

    return calls


def test_each_missing_language_is_one_piece_queued_once(store, saved):
    asyncio.run(translate_news(NEWS_ID, POST))
    asyncio.run(translate_news(NEWS_ID, POST))

    rows = sorted(store.rows.values(), key=lambda row: row.key)
    assert [(row.kind, row.key) for row in rows] == [(BatchKind.NEWS, "de"), (BatchKind.NEWS, "fr")]
    body = rows[0].body
    # The role and rules first, the post as data and the language last; a strict schema.
    assert body["messages"][0]["role"] == "system"
    assert body["messages"][0]["content"].startswith("You are")
    assert "Line one.\nLine two." in body["messages"][1]["content"]
    assert language_of(body) == "German"
    assert body["response_format"]["json_schema"]["strict"] is True


def test_a_reply_within_the_limits_goes_to_site_as_an_event_priced_at_batch_price(
    store, saved, monkeypatch, published
):
    """Each translation goes back as `news.translated`, with the English it's of, and no call
    to site."""
    asyncio.run(translate_news(NEWS_ID, POST))

    def answer(body):
        language = language_of(body)

        return json.dumps({"title": f" {language} title ", "text": f"{language} text"})

    run_batches(monkeypatch, answer)

    events = [call for call in saved if call != "published"]
    assert {kind for kind, _ in events} == {NEWS_TRANSLATED}
    assert sorted((data["translations"] for _, data in events), key=list) == [
        {"de": {"title": "German title", "text": "German text"}},
        {"fr": {"title": "French title", "text": "French text"}},
    ]
    assert {(data["news_id"], data["title"], data["text"]) for _, data in events} == {
        (str(NEWS_ID), POST.title, POST.text)
    }
    assert saved.count("published") == 2
    # What site reads it as.
    assert NewsTranslated.model_validate(events[0][1]).news_id == NEWS_ID
    assert store.rows == {}
    used = [data for kind, data in published if kind == AI_USED]
    assert {data["action"] for data in used} == {NEWS_TRANSLATION}
    assert {data["subject_id"] for data in used} == {str(NEWS_ID)}


def test_a_reply_past_the_limits_is_asked_for_again_then_given_up(store, saved, monkeypatch):
    asyncio.run(translate_news(NEWS_ID, POST))
    too_long = json.dumps({"title": "T", "text": "x" * (MAX_NEWS_TEXT_LENGTH + 1)})

    run_batches(monkeypatch, lambda body: too_long, rounds=BATCH_WORK_ATTEMPTS)

    assert saved == []
    assert store.rows == {}


def test_a_campaigns_translation_goes_to_notifications_as_an_event_without_a_made_up_button(
    store, saved, monkeypatch
):
    """Notifications sends the English and the missing languages; each translation goes back as
    `notification.campaign_translated`, with the English it's of, and no call to notifications."""
    asyncio.run(translate_campaign(CAMPAIGN_ID, CAMPAIGN))
    asyncio.run(translate_campaign(CAMPAIGN_ID, CAMPAIGN))
    reply = json.dumps({"subject": "Neu", "text": "Eins.\n\nZwei.", "button": "Erfunden"})

    run_batches(monkeypatch, lambda body: reply)

    [(kind, data), published] = saved
    assert (kind, published) == (CAMPAIGN_TRANSLATED, "published")
    assert data == {
        "campaign_id": str(CAMPAIGN_ID),
        "subject": "New",
        "text": "One.\n\nTwo.",
        "button": None,
        "translations": {"de": {"subject": "Neu", "text": "Eins.\n\nZwei.", "button": ""}},
    }
    # What notifications reads it as.
    assert CampaignTranslated.model_validate(data).campaign_id == CAMPAIGN_ID
    assert store.rows == {}
