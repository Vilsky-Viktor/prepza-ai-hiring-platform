from rounds.config import settings
from rounds.constants.rounds import CHAT_RETRIES, CHAT_TIMEOUT_SECONDS
from rounds.integrations import llm


def test_the_help_chat_uses_its_own_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    llm.get_help_llm.cache_clear()

    try:
        help_chat = llm.get_help_llm()

        assert help_chat.model_name == settings.help_model
        assert help_chat.reasoning_effort == settings.help_reasoning_effort == "none"
        assert help_chat.temperature == 0.3
        assert help_chat.request_timeout == CHAT_TIMEOUT_SECONDS
        assert help_chat.max_retries == CHAT_RETRIES
        # Every try ends within rounds' 60 s request timeout.
        assert (1 + CHAT_RETRIES) * CHAT_TIMEOUT_SECONDS < 60
    finally:
        llm.get_help_llm.cache_clear()


def test_the_help_chat_sends_no_temperature_when_it_reasons(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(settings, "help_reasoning_effort", "low")
    llm.get_help_llm.cache_clear()

    try:
        assert llm.get_help_llm().temperature is None
    finally:
        llm.get_help_llm.cache_clear()
