import asyncio
import uuid

import pytest

from app.constants.generation import LLM_MAX_RETRIES
from app.integrations import library, llm
from app.prompts import answers
from app.prompts import regenerate as regenerate_prompts
from app.schemas.questions import AnswerItem, AnswerList, NewQuestion
from app.schemas.regenerate import QuestionContext
from app.services import regenerate as regenerate_module
from app.services.regenerate import regenerate

QUESTION_ID = uuid.uuid4()


def context(multi=False, example=False):
    return QuestionContext(
        set_id=uuid.uuid4(),
        kind="preparation",
        owner_id="ann",
        level="medium",
        topic="Python",
        subtopics=["Asyncio"],
        existing=["What is the GIL?", "When is asyncio a good fit?"],
        multi=multi,
        example=example,
    )


class FakeStructured:
    """Writes the next of `questions`, then options of the kind the prompt asks for."""

    def __init__(self, schema, questions, prompts):
        self.schema = schema
        self.questions = questions
        self.prompts = prompts

    async def ainvoke(self, messages):
        prompt = "\n".join(message.content for message in messages)
        self.prompts.append(prompt)

        if self.schema is NewQuestion:
            # A question, or a (question, example) pair for one that shows an example.
            written = self.questions.pop(0)
            text, example = written if isinstance(written, tuple) else (written, None)

            return NewQuestion(
                question=text, example=example, example_language="python" if example else None
            )

        ambiguous = "[0] Which keyword" in prompt
        correct, distractors = (
            (["R1", "R2"], ["A", "B"])
            if answers.MULTI_ANSWER_KIND in prompt
            else (["R"], ["A", "B", "C"])
        )

        return AnswerList(
            answers=[
                AnswerItem(
                    id=0, correct_options=correct, distractors=distractors, ambiguous=ambiguous
                )
            ]
        )


class FakeEmbeddings:
    """Texts about the GIL mean the same thing; every other text means something of its own."""

    async def aembed_documents(self, texts):
        meanings = [
            "gil" if "gil" in text.lower() or "interpreter lock" in text.lower() else text
            for text in texts
        ]
        distinct = list(dict.fromkeys(meanings))

        return [
            [float(distinct.index(meaning) == i) for i in range(len(distinct))]
            for meaning in meanings
        ]


@pytest.fixture(autouse=True)
def fake_embeddings(monkeypatch):
    monkeypatch.setattr(llm, "get_embeddings", FakeEmbeddings)


class FakeLLM:
    def __init__(self, questions):
        self.questions = questions
        self.prompts = []

    def with_structured_output(self, schema):
        return FakeStructured(schema, self.questions, self.prompts)


def test_skips_duplicates_and_saves_new_question(monkeypatch):
    fake = FakeLLM(["  what is the  GIL? ", "How do you cancel an asyncio task?"])
    saved = {}

    async def fake_replace(question_id, question):
        saved["id"] = question_id
        saved["question"] = question

    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: fake)
    monkeypatch.setattr(library, "replace_question", fake_replace)

    result = asyncio.run(regenerate(QUESTION_ID, context()))

    assert result.text == "How do you cancel an asyncio task?"
    assert saved["id"] == QUESTION_ID
    assert sum(option.correct for option in saved["question"].options) == 1


@pytest.mark.parametrize("multi", [False, True])
def test_a_replacement_keeps_the_kind_of_the_question_it_replaces(monkeypatch, multi):
    fake = FakeLLM(["How do you cancel an asyncio task?"])
    saved = {}

    async def fake_replace(question_id, question):
        saved["question"] = question

    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: fake)
    monkeypatch.setattr(library, "replace_question", fake_replace)

    asyncio.run(regenerate(QUESTION_ID, context(multi)))

    question_prompt, answers_prompt = fake.prompts
    kinds = (regenerate_prompts.MULTI_ANSWER_KIND, answers.MULTI_ANSWER_KIND)

    assert sum(option.correct for option in saved["question"].options) == (2 if multi else 1)
    assert len(saved["question"].options) == 4
    assert (kinds[0] in question_prompt, kinds[1] in answers_prompt) == (multi, multi)


@pytest.mark.parametrize("example", [False, True])
def test_a_replacement_shows_an_example_when_the_question_it_replaces_did(monkeypatch, example):
    shown = ("What does this print?", "print(len([1, 2]))")
    plain = "When does asyncio.run return?"
    fake = FakeLLM([plain, shown] if example else [shown, plain])
    saved = {}

    async def fake_replace(question_id, question):
        saved["question"] = question

    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: fake)
    monkeypatch.setattr(library, "replace_question", fake_replace)

    asyncio.run(regenerate(QUESTION_ID, context(example=example)))

    asked = regenerate_prompts.WITH_EXAMPLE if example else regenerate_prompts.WITHOUT_EXAMPLE

    # The first one written is of the other kind, so it's written again.
    assert asked in fake.prompts[0]
    assert saved["question"].text == (
        "What does this print?\n```python\nprint(len([1, 2]))\n```" if example else plain
    )


def test_the_rewrite_is_told_what_users_reported_about_the_question(monkeypatch):
    fake = FakeLLM(["How do you cancel an asyncio task?", "What does asyncio.sleep(0) do?"])

    async def fake_replace(question_id, question):
        return None

    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: fake)
    monkeypatch.setattr(library, "replace_question", fake_replace)

    reasons = ["hard_to_read", "hard_to_read", "other"]
    asyncio.run(regenerate(QUESTION_ID, context(), reasons))
    told = fake.prompts[0]
    asyncio.run(regenerate(QUESTION_ID, context()))
    untold = fake.prompts[2]

    guidance = regenerate_prompts.REPORT_GUIDANCE["hard_to_read"]

    assert told.count(guidance) == 1
    assert "simple sentences" in guidance and "notation" in guidance
    assert guidance not in untold
    assert regenerate_prompts.REPORTS.split("\n")[0] not in untold


def test_skips_a_rephrased_existing_question(monkeypatch):
    fake = FakeLLM(["What does the global interpreter lock do?", "What does asyncio.run do?"])
    saved = {}

    async def fake_replace(question_id, question):
        saved["question"] = question

    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: fake)
    monkeypatch.setattr(library, "replace_question", fake_replace)

    result = asyncio.run(regenerate(QUESTION_ID, context()))

    assert result.text == "What does asyncio.run do?"
    assert saved["question"].text == "What does asyncio.run do?"


def test_ambiguous_question_is_replaced_by_another(monkeypatch):
    fake = FakeLLM(["Which keyword handles exceptions?", "What does asyncio.gather return?"])
    saved = {}

    async def fake_replace(question_id, question):
        saved["question"] = question

    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: fake)
    monkeypatch.setattr(library, "replace_question", fake_replace)

    result = asyncio.run(regenerate(QUESTION_ID, context()))

    assert result.text == "What does asyncio.gather return?"
    assert saved["question"].text == "What does asyncio.gather return?"


def test_gives_up_when_every_attempt_duplicates(monkeypatch):
    fake = FakeLLM(["What is the GIL?"] * 3)

    async def fake_replace(question_id, question):
        raise AssertionError("must not save a duplicate")

    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: fake)
    monkeypatch.setattr(library, "replace_question", fake_replace)

    assert asyncio.run(regenerate(QUESTION_ID, context())) is None


def test_a_regeneration_past_its_deadline_replaces_nothing(monkeypatch):
    """The caller gives up at 120 s: writing that runs longer leaves the question as it was, so
    trying again never makes two replacements."""
    replaced = []

    async def slow_write(_context, _reasons):
        await asyncio.sleep(1)

        return "A late question?", ["a", "b", "c", "d"]

    async def fake_replace(question_id, question):
        replaced.append(question_id)

    monkeypatch.setattr(regenerate_module, "write", slow_write)
    monkeypatch.setattr(regenerate_module, "REGENERATE_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(library, "replace_question", fake_replace)

    assert asyncio.run(regenerate(QUESTION_ID, context())) is None
    assert replaced == []


def test_a_failed_ai_call_is_retried_a_few_times_only(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    llm.build_llm.cache_clear()

    assert llm.build_llm("gpt-test", "low").max_retries == LLM_MAX_RETRIES == 2
