"""Flagged questions rewritten, or given new options, through OpenAI's Batch API
(services/verify.py, batch_work.py, batch_steps.py): the new question first, then its options,
each checked as the direct calls check them, and saved only while the question is still the one
flagged. OpenAI, the library and storage are fakes."""

import asyncio

import pytest

from app.constants.batch_work import BATCH_WORK_ATTEMPTS, BatchKind, BatchStep
from app.constants.quality import QualityFlag
from app.integrations import library
from app.schemas.questions import AnswerItem, AnswerList, NewQuestion
from app.services import regenerate
from app.services.verify import verify
from tests.unit.batch_fakes import run_batches
from tests.unit.test_verify import QUESTION_ID, TEXT, context, question

NEW = "A supplier invoice arrives. Which entry records it?"
OPTIONS = AnswerList(
    answers=[
        AnswerItem(
            id=0,
            correct_options=["Credit payables"],
            distractors=["Debit payables", "Credit cash", "Debit revenue"],
            ambiguous=False,
        )
    ]
)
AMBIGUOUS = AnswerList(
    answers=[AnswerItem(id=0, correct_options=[], distractors=[], ambiguous=True)]
)


@pytest.fixture
def flagged(monkeypatch):
    """The library: the question flagged for a rewrite, and what was saved in its place."""
    state = {"flag": QualityFlag.REWRITE, "text": TEXT, "saved": []}

    async def get_context(question_id):
        return context()

    async def get_quality(question_id):
        return question().model_copy(update={"flag": state["flag"], "text": state["text"]})

    async def replace_question(question_id, new):
        state["saved"].append((question_id, new.text, [o.correct for o in new.options]))

    async def distinct(texts, keep_first=0):
        return list(range(len(texts)))

    monkeypatch.setattr(library, "get_question_context", get_context)
    monkeypatch.setattr(library, "get_question_quality", get_quality)
    monkeypatch.setattr(library, "replace_question", replace_question)
    monkeypatch.setattr(regenerate, "distinct_by_meaning", distinct)

    return state


def answering(*replies):
    """OpenAI answering each request with the next reply, by the schema it asks for."""
    queue = list(replies)

    def answer(body):
        return queue.pop(0).model_dump_json() if queue else None

    return answer


def written(text: str) -> NewQuestion:
    return NewQuestion(question=text, example=None, example_language=None)


def test_a_rewrite_writes_a_question_then_its_options_and_saves_them(
    monkeypatch, flagged, batch_store
):
    asyncio.run(verify(QUESTION_ID, QualityFlag.REWRITE))

    [row] = batch_store.rows.values()
    assert (row.kind, row.step) == (BatchKind.REWRITE, BatchStep.QUESTION)
    # The reports' reasons reach the new question's prompt; their comments never do.
    assert "Cash comes in" not in str(row.body)

    run_batches(monkeypatch, answering(written(NEW), OPTIONS), rounds=2)

    [(saved_id, text, correct)] = flagged["saved"]
    assert (saved_id, text, sorted(correct)) == (QUESTION_ID, NEW, [False, False, False, True])
    assert batch_store.rows == {}


def test_a_question_that_repeats_one_is_asked_for_again_unlike_it(
    monkeypatch, flagged, batch_store
):
    asyncio.run(verify(QUESTION_ID, QualityFlag.REWRITE))

    run_batches(monkeypatch, answering(written(TEXT)), rounds=1)

    [row] = batch_store.rows.values()
    assert (row.step, row.attempt) == (BatchStep.QUESTION, 1)
    assert row.payload["existing"][-1] == TEXT


def test_ambiguous_new_options_turn_into_a_rewrite_never_offering_that_question_again(
    monkeypatch, flagged, batch_store
):
    flagged["flag"] = QualityFlag.WEAK_OPTIONS
    asyncio.run(verify(QUESTION_ID, QualityFlag.WEAK_OPTIONS))

    run_batches(monkeypatch, answering(AMBIGUOUS), rounds=1)

    [row] = batch_store.rows.values()
    assert row.step == BatchStep.QUESTION
    assert TEXT in row.payload["existing"]


def test_a_question_kept_or_edited_since_it_was_flagged_keeps_its_own(
    monkeypatch, flagged, batch_store
):
    asyncio.run(verify(QUESTION_ID, QualityFlag.REWRITE))
    flagged["flag"] = None

    run_batches(monkeypatch, answering(written(NEW), OPTIONS), rounds=2)

    assert flagged["saved"] == []
    assert batch_store.rows == {}


def test_work_that_keeps_coming_back_unusable_is_given_up(monkeypatch, flagged, batch_store):
    asyncio.run(verify(QUESTION_ID, QualityFlag.REWRITE))

    run_batches(monkeypatch, lambda body: None, rounds=BATCH_WORK_ATTEMPTS)

    assert flagged["saved"] == []
    assert batch_store.rows == {}


def test_a_flag_sent_twice_queues_its_work_once(monkeypatch, flagged, batch_store):
    asyncio.run(verify(QUESTION_ID, QualityFlag.REWRITE))
    asyncio.run(verify(QUESTION_ID, QualityFlag.REWRITE))

    assert len(batch_store.rows) == 1
