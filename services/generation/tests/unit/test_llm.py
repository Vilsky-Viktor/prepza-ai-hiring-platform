import pytest

from app.config.settings import settings
from app.constants.generation import LLM_TIMEOUT_SECONDS
from app.integrations import llm


@pytest.fixture(autouse=True)
def models(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setattr(settings, "interview_model", "interview-model")
    llm.build_llm.cache_clear()
    yield
    llm.build_llm.cache_clear()


def test_llm_calls_time_out():
    assert llm.get_generation_llm().request_timeout == LLM_TIMEOUT_SECONDS


def test_each_task_uses_its_own_model_and_effort(monkeypatch):
    monkeypatch.setattr(settings, "interview_reasoning_effort", "high")
    tasks = {
        "verify": llm.get_verifier_llm,
        "translation": llm.get_translation_llm,
        "patterns": llm.get_patterns_llm,
        "code_tags": llm.get_code_tags_llm,
    }

    for name in tasks:
        monkeypatch.setattr(settings, f"{name}_model", f"{name}-model")
        monkeypatch.setattr(settings, f"{name}_reasoning_effort", "minimal")

    assert (llm.get_generation_llm().model_name, llm.get_generation_llm().reasoning_effort) == (
        "interview-model",
        "high",
    )

    for name, getter in tasks.items():
        assert (getter().model_name, getter().reasoning_effort) == (f"{name}-model", "minimal")
