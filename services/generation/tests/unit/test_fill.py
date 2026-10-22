import asyncio
import uuid

import pytest
from prepza_common.multi_answer import is_multi

from app.helpers.payload import build_preparation
from app.integrations import llm
from app.services.nodes.fill import fill_topics
from app.services.top_up import TopicShortError
from tests.unit.fakes import EXAMPLE, OPTIONS, FakeVerifier, asked_examples, asked_multi, items


class FakeStructured:
    def __init__(self, questions, prompts, writes_multi):
        self.questions = questions
        self.prompts = prompts
        self.writes_multi = writes_multi

    async def ainvoke(self, messages):
        prompt = messages[-1].content
        self.prompts.append(prompt)
        multi = asked_multi(prompt) if self.writes_multi else 0

        return items(self.questions, multi, asked_examples(prompt))


class FakeLLM:
    """Writes `questions` every call, as many multi-answer as asked unless `writes_multi` is
    off."""

    def __init__(self, questions, writes_multi=True):
        self.questions = questions
        self.writes_multi = writes_multi
        self.prompts = []

    def with_structured_output(self, schema):
        return FakeStructured(self.questions, self.prompts, self.writes_multi)


def state(usable, dropped=0, examples=0, share=0):
    """One topic with `usable` answered questions, the first `examples` of them with an example,
    and `dropped` ones that have no options; `share` of a topic is multi-answer."""
    questions = [
        f"Question {i}" + (EXAMPLE if i < examples else "") for i in range(usable + dropped)
    ]
    options = [OPTIONS] * usable + [[]] * dropped

    return {
        "level": "basic",
        # Ten questions a topic, as the run started with them.
        "topic_size": 10,
        "multi_share": share,
        "title": "Bookkeeping",
        "requirements": [],
        "final": [
            {
                "topic": "Bookkeeping",
                "subtopics": ["Cash"],
                "questions": questions,
                "answer_options": options,
            }
        ],
    }


@pytest.fixture(autouse=True)
def verifier(monkeypatch):
    monkeypatch.setattr(llm, "get_verifier_llm", FakeVerifier)


def test_a_short_topic_is_filled_to_exactly_its_size(monkeypatch):
    # One returned question repeats an existing one, so only three are new.
    fake = FakeLLM(["Question 0", "New 1", "New 2", "New 3"])
    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: fake)
    values = state(usable=7, dropped=2)

    values.update(asyncio.run(fill_topics(values)))
    payload = build_preparation(uuid.uuid4(), "uid", "text", values)

    assert [q.text for q in payload.topics[0].questions][-3:] == ["New 1", "New 2", "New 3"]
    assert len(payload.topics[0].questions) == 10
    assert "- Question 8" in fake.prompts[0]


def test_a_full_topic_is_left_alone(monkeypatch):
    fake = FakeLLM(["Never asked"])
    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: fake)
    values = state(usable=10)

    assert asyncio.run(fill_topics(values))["final"] == values["final"]
    assert fake.prompts == []


def test_a_topic_that_cannot_be_filled_fails_the_generation(monkeypatch):
    fake = FakeLLM(["Question 0", "Question 1"])
    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: fake)

    with pytest.raises(TopicShortError):
        asyncio.run(fill_topics(state(usable=8)))

    assert len(fake.prompts) == 3


def test_a_short_topic_is_topped_up_with_each_kind_it_lacks(monkeypatch):
    # Two of ten are multi-answer; seven single-answer ones lack one single and two multi.
    fake = FakeLLM(["Question 0", "New 1", "New 2", "New 3"])
    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: fake)

    [item] = asyncio.run(fill_topics(state(usable=7, share=0.2)))["final"]

    assert item["questions"][7:] == ["New 1", "New 2", "New 3"]
    assert [is_multi(options) for options in item["answer_options"][7:]] == [False, True, True]
    # One call asks only for single-answer questions, the other only for multi-answer ones.
    assert [asked_multi(prompt) for prompt in fake.prompts] == [0, 4]


def test_multi_answer_questions_that_never_come_are_made_up_with_single_in_the_last_round(
    monkeypatch,
):
    fake = FakeLLM(["New 1", "New 2", "New 3", "New 4", "New 5"], writes_multi=False)
    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: fake)

    [item] = asyncio.run(fill_topics(state(usable=8, share=0.2)))["final"]

    assert len(item["questions"]) == 10
    assert not any(is_multi(options) for options in item["answer_options"])
    # Two rounds ask for the multi-answer ones; the last asks for single-answer ones instead.
    assert [asked_multi(prompt) for prompt in fake.prompts] == [4, 4, 0]


def test_a_topic_on_formal_material_is_topped_up_with_the_examples_it_lacks(monkeypatch):
    # Two of seven show code, so the topic is held to at least 3 of 10 with an example.
    fake = FakeLLM(["New 1", "New 2", "New 3", "New 4", "New 5"])
    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: fake)

    [item] = asyncio.run(fill_topics(state(usable=7, examples=2)))["final"]

    shown = [text for text in item["questions"] if "```" in text]

    assert len(item["questions"]) == 10
    assert len(shown) == 3
    # One call asks only for ones with an example, the other only for ones without.
    assert sorted(asked_examples(prompt) for prompt in fake.prompts) == [0, 3]


def test_a_topic_on_other_material_is_never_asked_for_examples(monkeypatch):
    fake = FakeLLM(["New 1", "New 2", "New 3", "New 4", "New 5"])
    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: fake)

    [item] = asyncio.run(fill_topics(state(usable=7)))["final"]

    assert len(item["questions"]) == 10
    assert [asked_examples(prompt) for prompt in fake.prompts] == [0]
