import pytest
from langchain_core.messages import AIMessage, HumanMessage
from prepza_common.ai.llm import (
    call_cost,
    chat_model,
    estimated_input,
    estimated_tokens,
    latest_messages,
    transcription_cost,
)


@pytest.fixture(autouse=True)
def openai_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")


def test_a_model_takes_a_temperature_at_effort_none():
    model = chat_model("model-a", "none", temperature=0.3, timeout=60, max_retries=3)

    assert (model.model_name, model.reasoning_effort, model.temperature) == ("model-a", "none", 0.3)
    assert (model.request_timeout, model.max_retries) == (60, 3)


@pytest.mark.parametrize("effort", ["minimal", "low", "medium", "high"])
def test_a_reasoning_model_gets_no_temperature(effort):
    model = chat_model("model-a", effort, temperature=0.3)

    assert model.reasoning_effort == effort
    assert model.temperature is None


def test_without_a_temperature_none_is_sent():
    assert chat_model("model-a", "none").temperature is None


def test_nothing_is_stored_at_openai():
    assert chat_model("model-a", "low").store is False


def test_a_call_costs_its_tokens_at_the_models_price():
    usage = {"input_tokens": 1_000_000, "output_tokens": 100_000}

    assert call_cost("gpt-6.1-sol", usage) == 2.0 + 1.0
    assert call_cost("unknown-model", usage) is None


def test_only_the_latest_messages_that_fit_are_kept():
    messages = [(True, "x" * 50), (False, "y" * 30), (True, "z" * 30)]

    assert latest_messages(messages, 70) == [
        AIMessage(content="y" * 30),
        HumanMessage(content="z" * 30),
    ]


def test_a_message_without_text_adds_nothing():
    assert latest_messages([(True, "Hi"), (False, "")], 1_000) == [HumanMessage(content="Hi")]


def test_a_call_cut_short_is_estimated_at_four_characters_a_token():
    assert estimated_tokens("") == 0
    assert estimated_tokens("abcde") == 2
    assert estimated_input([HumanMessage(content="abcd"), AIMessage(content="efgh")]) == 2


def test_cached_input_costs_its_own_price():
    usage = {
        "input_tokens": 1_000_000,
        "input_token_details": {"cache_read": 400_000},
        "output_tokens": 0,
    }

    # 600k fresh at $2.00 and 400k cached at $0.20 a million.
    assert call_cost("gpt-6.1-sol", usage) == pytest.approx(1.2 + 0.08)


def test_a_batch_api_call_costs_half():
    usage = {"input_tokens": 1_000_000, "output_tokens": 100_000}

    assert call_cost("gpt-6.1-sol", usage, batch=True) == pytest.approx(1.5)


def test_a_dated_model_costs_its_models_price():
    usage = {"input_tokens": 1_000_000, "output_tokens": 0}

    assert call_cost("gpt-6-luna-2026-08-01", usage) == pytest.approx(0.10)
    assert call_cost("gpt-6-lunar", usage) is None


def test_embeddings_cost_their_input_only():
    usage = {"input_tokens": 1_000_000, "output_tokens": 0}

    assert call_cost("text-embedding-3-small", usage) == pytest.approx(0.02)


def test_transcription_costs_by_the_minute():
    assert transcription_cost("gpt-4o-mini-transcribe", 90) == pytest.approx(0.0045)
    assert transcription_cost("unknown-model", 90) is None
