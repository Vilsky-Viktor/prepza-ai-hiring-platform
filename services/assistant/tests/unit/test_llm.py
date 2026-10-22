import pytest

from app.integrations import llm


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
