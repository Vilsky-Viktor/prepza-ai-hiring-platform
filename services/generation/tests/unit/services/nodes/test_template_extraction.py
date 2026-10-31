import asyncio
from types import SimpleNamespace

from testee_common.config.constants import MAX_TITLE_LENGTH

from generation.integrations import llm
from generation.repositories import draft_cache
from generation.services.nodes import extraction


def messages_for(monkeypatch, template):
    """The extraction messages the model gets for a test, or for a template."""
    seen = []

    class FakeLLM:
        def with_structured_output(self, schema):
            return self

        async def ainvoke(self, messages):
            seen.append(messages)

            return SimpleNamespace(title="Accountant", requirements=["IFRS"], level="medium")

    async def no_cache(*args):
        return None

    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: FakeLLM())
    monkeypatch.setattr(draft_cache, "get", no_cache)
    monkeypatch.setattr(draft_cache, "put", no_cache)
    state = {"input_text": "Acme hires an accountant.", "language": "en", "template": template}

    asyncio.run(extraction.extract_info(state))

    return seen[0]


def test_the_instructions_are_the_same_and_the_posting_is_data_in_the_request(monkeypatch):
    template = messages_for(monkeypatch, True)
    test = messages_for(monkeypatch, False)

    # One system message for both kinds (the provider caches it), the role first.
    assert template[0].content == test[0].content
    assert template[0].content.startswith("You are")
    assert "Acme" not in template[0].content
    # The posting is tagged; the kind and the language come last, and differ.
    assert "<job_posting>\nAcme hires an accountant.\n</job_posting>" in template[1].content
    assert template[1].content != test[1].content
    assert template[1].content.rstrip().endswith("in English.")


def test_a_title_too_long_is_cut_to_what_editing_it_allows(monkeypatch):
    """Fresh from the model or from the cache: saving the paid-for questions never fails on it."""
    long = "Senior Accountant " * 10

    class FakeLLM:
        def with_structured_output(self, schema):
            return self

        async def ainvoke(self, messages):
            return SimpleNamespace(title=long, requirements=["IFRS"], level="medium")

    async def no_cache(*args):
        return None

    async def cached(*args):
        return {"title": long, "requirements": ["IFRS"], "level": "medium"}

    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: FakeLLM())
    monkeypatch.setattr(draft_cache, "put", no_cache)
    state = {"input_text": "Acme hires an accountant.", "language": "en"}

    for found in (no_cache, cached):
        monkeypatch.setattr(draft_cache, "get", found)
        title = asyncio.run(extraction.extract_info(state))["title"]

        assert len(title) <= MAX_TITLE_LENGTH
        assert title.startswith("Senior Accountant")
