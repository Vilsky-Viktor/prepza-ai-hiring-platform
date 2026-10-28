import pytest

from assistant.constants.help_chat import HELP_MAX_OUTPUT_TOKENS, HELP_RETRIES, HELP_TIMEOUT_SECONDS
from assistant.integrations import llm


@pytest.fixture(autouse=True)
def openai_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    llm.get_chat_model.cache_clear()
    yield
    llm.get_chat_model.cache_clear()


def test_the_assistant_stores_nothing_at_openai_and_sends_its_reasoning_back():
    model = llm.get_chat_model()

    assert model.store is False
    assert model.include == ["reasoning.encrypted_content"]


def test_titles_use_their_own_model_and_effort(monkeypatch):
    monkeypatch.setattr(llm.settings, "title_model", "title-model")
    monkeypatch.setattr(llm.settings, "title_reasoning_effort", "minimal")
    llm.get_title_model.cache_clear()
    model = llm.get_title_model()
    llm.get_title_model.cache_clear()

    assert (model.model_name, model.reasoning_effort) == ("title-model", "minimal")


@pytest.fixture
def help_llm():
    llm.get_help_llm.cache_clear()
    yield
    llm.get_help_llm.cache_clear()


def test_the_help_chat_uses_its_own_model_capped_and_reporting_its_tokens(help_llm):
    help_chat = llm.get_help_llm()

    assert help_chat.model_name == llm.settings.help_model
    assert help_chat.reasoning_effort == llm.settings.help_reasoning_effort == "none"
    assert help_chat.temperature == 0.3
    assert help_chat.request_timeout == HELP_TIMEOUT_SECONDS
    assert help_chat.max_retries == HELP_RETRIES
    assert help_chat.max_tokens == HELP_MAX_OUTPUT_TOKENS
    assert help_chat.stream_usage is True
    # Every try ends well within the assistant's 300 s request timeout.
    assert (1 + HELP_RETRIES) * HELP_TIMEOUT_SECONDS < 300


def test_the_help_chat_sends_no_temperature_when_it_reasons(help_llm, monkeypatch):
    monkeypatch.setattr(llm.settings, "help_reasoning_effort", "low")

    assert llm.get_help_llm().temperature is None
