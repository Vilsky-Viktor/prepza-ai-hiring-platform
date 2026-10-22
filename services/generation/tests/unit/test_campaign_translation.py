import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from prepza_common.constants import MAX_CAMPAIGN_BUTTON_LENGTH
from prepza_common.http import bearer

from app.constants.generation import TRANSLATE_CAMPAIGN
from app.integrations import llm, notifications
from app.schemas.campaigns import CampaignSource, TranslatedCampaign
from app.services.campaigns import translate_campaign

CAMPAIGN_ID = uuid.uuid4()
SOURCE = CampaignSource(
    subject="New: code questions", text="One.\n\nTwo.", button="See it", missing=["de", "fr"]
)


class FakeLLM:
    """Translates by naming the language; `bad` maps a language to what goes wrong in it."""

    def __init__(self, bad=None):
        self.bad = bad or {}
        self.prompts = []

    def with_structured_output(self, schema):
        assert schema is TranslatedCampaign

        return self

    async def ainvoke(self, messages):
        self.prompts.append(messages)
        prompt = messages[-1].content
        language = prompt.split(" into ", 1)[1].split(".", 1)[0]
        problem = self.bad.get(language)

        if problem == "error":
            raise RuntimeError("model down")

        button = "x" * (MAX_CAMPAIGN_BUTTON_LENGTH + 1) if problem == "too long" else language

        return TranslatedCampaign(subject=f" {language} ", text=f"{language} text", button=button)


@pytest.fixture
def saved(monkeypatch):
    calls = []
    state = {"source": SOURCE}

    async def get_campaign_source(campaign_id):
        return state["source"]

    async def save_campaign_translations(campaign_id, source, translations):
        calls.append((campaign_id, source, translations))

    monkeypatch.setattr(notifications, "get_campaign_source", get_campaign_source)
    monkeypatch.setattr(notifications, "save_campaign_translations", save_campaign_translations)

    return calls, state


def test_each_missing_language_is_translated_and_saved(monkeypatch, saved):
    calls, _ = saved
    model = FakeLLM()
    monkeypatch.setattr(llm, "get_translation_llm", lambda: model)

    asyncio.run(translate_campaign(CAMPAIGN_ID))

    [(campaign_id, source, translations)] = calls
    assert (campaign_id, source) == (CAMPAIGN_ID, SOURCE)
    assert {code: (item.subject, item.button) for code, item in translations.items()} == {
        "de": ("German", "German"),
        "fr": ("French", "French"),
    }
    # The role and rules first, the text as data and the language last in the user's message.
    for system, user in model.prompts:
        assert system.type == "system" and system.content.startswith("You are")
        assert "One.\n\nTwo." in user.content and "One.\n\nTwo." not in system.content
        assert user.content.rstrip().endswith(("German.", "French."))


def test_a_campaign_without_a_button_gets_none(monkeypatch, saved):
    calls, state = saved
    state["source"] = SOURCE.model_copy(update={"button": None})
    monkeypatch.setattr(llm, "get_translation_llm", lambda: FakeLLM())

    asyncio.run(translate_campaign(CAMPAIGN_ID))

    [(_, _, translations)] = calls
    assert {item.button for item in translations.values()} == {""}


@pytest.mark.parametrize("problem", ["error", "too long"])
def test_a_failed_language_is_left_out_and_the_job_fails_to_be_retried(monkeypatch, saved, problem):
    calls, _ = saved
    monkeypatch.setattr(llm, "get_translation_llm", lambda: FakeLLM({"French": problem}))

    with pytest.raises(RuntimeError):
        asyncio.run(translate_campaign(CAMPAIGN_ID))

    [(_, _, translations)] = calls
    assert list(translations) == ["de"]


def test_a_sent_or_deleted_campaign_needs_nothing(monkeypatch, saved):
    calls, state = saved

    def no_model():
        raise AssertionError("no translation needed")

    monkeypatch.setattr(llm, "get_translation_llm", no_model)

    for found in (None, SOURCE.model_copy(update={"missing": []})):
        state["source"] = found
        asyncio.run(translate_campaign(CAMPAIGN_ID))

    assert calls == []


def test_the_translate_endpoint_queues_the_worker_job(client, queued):
    exp = datetime.now(UTC) + timedelta(seconds=60)
    token = jwt.encode(
        {"iss": "notifications", "aud": "generation", "exp": exp},
        "test-secret-that-is-at-least-32-bytes",
        algorithm="HS256",
    )

    assert client.post(f"/internal/campaigns/{CAMPAIGN_ID}/translate").status_code == 401

    response = client.post(f"/internal/campaigns/{CAMPAIGN_ID}/translate", headers=bearer(token))

    assert response.status_code == 202
    assert queued == [(TRANSLATE_CAMPAIGN, {"campaign_id": str(CAMPAIGN_ID)})]
