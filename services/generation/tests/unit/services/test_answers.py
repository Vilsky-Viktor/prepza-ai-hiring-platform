import asyncio

from generation.constants.generation import MAX_OPTION_CHARS
from generation.integrations import llm
from generation.prompts.answers import MULTI_ANSWER_KIND, SINGLE_ANSWER_KIND
from generation.schemas.questions import AnswerItem, AnswerList
from generation.services.answers import generate_answers

TOO_LONG = "x" * (MAX_OPTION_CHARS + 1)


class FakeStructured:
    """First reply has a correct option over the limit; the retry has a short one."""

    def __init__(self):
        self.calls = 0

    async def ainvoke(self, messages):
        self.calls += 1
        correct = TOO_LONG if self.calls == 1 else "Short and right"

        return AnswerList(
            answers=[
                AnswerItem(
                    id=0, correct_options=[correct], distractors=["A", "B", "C"], ambiguous=False
                )
            ]
        )


class FakeLLM:
    def __init__(self):
        self.structured = FakeStructured()

    def with_structured_output(self, schema):
        return self.structured


def test_correct_option_over_the_limit_is_retried(monkeypatch):
    fake = FakeLLM()
    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: fake)

    result = asyncio.run(
        generate_answers(
            {
                "topic_index": 0,
                "topic": "Topic",
                "start": 0,
                "questions": ["Question?"],
                "level": "medium",
            }
        )
    )
    [options] = result["answer_pool"][0]["options"]

    assert fake.structured.calls == 2
    assert [option["answer"] for option in options if option["correct"]] == ["Short and right"]
    assert all(len(option["answer"]) <= MAX_OPTION_CHARS for option in options)


class AmbiguousStructured:
    def __init__(self):
        self.calls = 0

    async def ainvoke(self, messages):
        self.calls += 1

        return AnswerList(
            answers=[
                AnswerItem(
                    id=0,
                    correct_options=["try"],
                    distractors=["catch", "finally", "except"],
                    ambiguous=True,
                ),
                AnswerItem(
                    id=1, correct_options=["Right"], distractors=["A", "B", "C"], ambiguous=False
                ),
            ]
        )


def test_ambiguous_question_is_dropped_without_retry(monkeypatch):
    fake = FakeLLM()
    fake.structured = AmbiguousStructured()
    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: fake)

    result = asyncio.run(
        generate_answers(
            {
                "topic_index": 0,
                "topic": "Python",
                "start": 0,
                "questions": ["Which keyword is used to handle exceptions?", "Clear question?"],
                "level": "medium",
            }
        )
    )
    ambiguous, clear = result["answer_pool"][0]["options"]

    assert fake.structured.calls == 1
    assert ambiguous == []
    assert len(clear) == 4


class ReplyInTurn:
    """Answers each call with the next of `replies` (correct_options, distractors)."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.prompts = []

    async def ainvoke(self, messages):
        self.prompts.append("\n".join(message.content for message in messages))
        correct, distractors = self.replies.pop(0)

        return AnswerList(
            answers=[
                AnswerItem(id=0, correct_options=correct, distractors=distractors, ambiguous=False)
            ]
        )


def options_for(monkeypatch, multi, *replies):
    fake = FakeLLM()
    fake.structured = ReplyInTurn(*replies)
    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: fake)
    result = asyncio.run(
        generate_answers(
            {
                "topic_index": 0,
                "topic": "Topic",
                "start": 0,
                "questions": ["Question?"],
                "level": "medium",
                "multi": multi,
            }
        )
    )

    return result["answer_pool"][0]["options"][0], fake.structured.prompts


def test_options_of_the_other_kind_are_retried(monkeypatch):
    # A multi-answer question needs 2 or 3 right; one right comes back first.
    options, prompts = options_for(
        monkeypatch, True, (["R1"], ["A", "B", "C"]), (["R1", "R2"], ["A", "B"])
    )

    assert sorted(option["answer"] for option in options if option["correct"]) == ["R1", "R2"]
    assert len(options) == 4
    assert len(prompts) == 2
    assert MULTI_ANSWER_KIND in prompts[0]

    # A single-answer question needs exactly one right.
    options, prompts = options_for(
        monkeypatch, False, (["R1", "R2"], ["A", "B"]), (["R1"], ["A", "B", "C"])
    )

    assert [option["answer"] for option in options if option["correct"]] == ["R1"]
    assert len(prompts) == 2
    assert SINGLE_ANSWER_KIND in prompts[0]


def test_a_multi_answer_question_with_every_option_right_is_retried(monkeypatch):
    options, prompts = options_for(
        monkeypatch, True, (["R1", "R2", "R3", "R4"], []), (["R1", "R2", "R3"], ["A"])
    )

    assert sorted(option["correct"] for option in options) == [False, True, True, True]
    assert len(prompts) == 2
