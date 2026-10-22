import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from prepza_common.constants import MAX_NEWS_TEXT_LENGTH
from prepza_common.http import bearer

from app.constants.generation import TRANSLATE_NEWS
from app.integrations import library, llm
from app.schemas.news import NewsSource, TranslatedNews
from app.services.news import translate_news

NEWS_ID = uuid.uuid4()
SOURCE = NewsSource(title="Practice in Thai", text="Line one.\nLine two.", missing=["de", "fr"])


class FakeLLM:
    """Translates by naming the language; `bad` maps a language to what goes wrong in it."""

    def __init__(self, bad=None):
        self.bad = bad or {}
        self.prompts = []

    def with_structured_output(self, schema):
        assert schema is TranslatedNews

        return self

    async def ainvoke(self, messages):
        prompt = messages[0].content
        self.prompts.append(prompt)
        language = prompt.split(" into ", 1)[1].split(".", 1)[0]
        problem = self.bad.get(language)

        if problem == "error":
            raise RuntimeError("model down")

        text = "x" * (MAX_NEWS_TEXT_LENGTH + 1) if problem == "too long" else f"{language} text"

        return TranslatedNews(title=f" {language} title ", text=text)


@pytest.fixture
def saved(monkeypatch):
    calls = []

    async def get_news_source(news_id):
        return SOURCE

    async def save_news_translations(news_id, source, translations):
        calls.append((news_id, source, translations))

    monkeypatch.setattr(library, "get_news_source", get_news_source)
    monkeypatch.setattr(library, "save_news_translations", save_news_translations)

    return calls


def test_each_missing_language_is_translated_and_saved(monkeypatch, saved):
    model = FakeLLM()
    monkeypatch.setattr(llm, "get_translation_llm", lambda: model)

    asyncio.run(translate_news(NEWS_ID))

    [(news_id, source, translations)] = saved
    assert (news_id, source) == (NEWS_ID, SOURCE)
    assert {code: item.title for code, item in translations.items()} == {
        "de": "German title",
        "fr": "French title",
    }
    assert all("Line one.\nLine two." in prompt for prompt in model.prompts)
    assert all('Keep "prepza" exactly as written' in prompt for prompt in model.prompts)


@pytest.mark.parametrize("problem", ["error", "too long"])
def test_a_failed_language_is_left_out_and_the_job_fails_to_be_retried(monkeypatch, saved, problem):
    monkeypatch.setattr(llm, "get_translation_llm", lambda: FakeLLM({"French": problem}))

    with pytest.raises(RuntimeError):
        asyncio.run(translate_news(NEWS_ID))

    [(_, _, translations)] = saved
    assert list(translations) == ["de"]


def test_a_deleted_or_translated_post_needs_nothing(monkeypatch, saved):
    def no_model():
        raise AssertionError("no translation needed")

    monkeypatch.setattr(llm, "get_translation_llm", no_model)

    for found in (None, SOURCE.model_copy(update={"missing": []})):

        async def get_news_source(news_id, found=found):
            return found

        monkeypatch.setattr(library, "get_news_source", get_news_source)
        asyncio.run(translate_news(NEWS_ID))

    assert saved == []


def test_the_translate_endpoint_queues_the_worker_job(client, queued):
    exp = datetime.now(UTC) + timedelta(seconds=60)
    service_token = jwt.encode(
        {"iss": "library", "aud": "generation", "exp": exp},
        "test-secret-that-is-at-least-32-bytes",
        algorithm="HS256",
    )

    assert client.post(f"/internal/news/{NEWS_ID}/translate").status_code == 401

    response = client.post(
        f"/internal/news/{NEWS_ID}/translate",
        headers=bearer(service_token),
    )

    assert response.status_code == 202
    assert queued == [(TRANSLATE_NEWS, {"news_id": str(NEWS_ID)})]
