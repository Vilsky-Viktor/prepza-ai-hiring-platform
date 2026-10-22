import asyncio
from types import SimpleNamespace

from openai import LengthFinishReasonError

from app.integrations import llm
from app.schemas.questions import AnswerItem, AnswerList, QuestionItem, QuestionItemList
from app.services.answers import generate_answers
from app.services.nodes.questions import generate_questions


def too_long() -> LengthFinishReasonError:
    return LengthFinishReasonError(completion=SimpleNamespace(usage=None))


class FakeLLM:
    """Replies in order: an exception is raised, anything else is returned."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def with_structured_output(self, schema):
        return self

    async def ainvoke(self, messages):
        self.calls += 1
        reply = self.replies.pop(0)

        if isinstance(reply, Exception):
            raise reply

        return reply


def items(*texts):
    return QuestionItemList(
        items=[
            QuestionItem(
                question=text,
                example=None,
                example_language=None,
                correct_options=["Right"],
                distractors=["A", "B", "C"],
                ambiguous=False,
            )
            for text in texts
        ]
    )


def question_task(count=3):
    return {
        "topic_index": 0,
        "topic": "Bookkeeping",
        "subtopic_index": 0,
        "subtopic": "Reconciliation",
        "count": count,
        "level": "medium",
    }


def test_looping_question_call_is_retried_and_trimmed_to_the_count(monkeypatch):
    fake = FakeLLM([too_long(), items("Q1", "Q2", "Q3", "Q4", "Q5")])
    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: fake)

    result = asyncio.run(generate_questions(question_task(count=3)))

    questions = result["question_pool"][0]["questions"]

    assert fake.calls == 2
    assert [question["text"] for question in questions] == ["Q1", "Q2", "Q3"]
    assert all(len(question["options"]) == 4 for question in questions)


def test_subtopic_that_always_loops_adds_nothing_instead_of_failing(monkeypatch):
    fake = FakeLLM([too_long(), too_long(), too_long()])
    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: fake)

    result = asyncio.run(generate_questions(question_task()))

    assert fake.calls == 3
    assert result["question_pool"][0]["questions"] == []


def test_looping_options_call_is_retried(monkeypatch):
    answers = AnswerList(
        answers=[
            AnswerItem(
                id=0, correct_options=["Right"], distractors=["A", "B", "C"], ambiguous=False
            )
        ]
    )
    fake = FakeLLM([too_long(), answers])
    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: fake)

    result = asyncio.run(
        generate_answers(
            {
                "topic_index": 0,
                "topic": "Bookkeeping",
                "start": 0,
                "questions": ["Question?"],
                "level": "medium",
            }
        )
    )

    assert fake.calls == 2
    assert len(result["answer_pool"][0]["options"][0]) == 4
