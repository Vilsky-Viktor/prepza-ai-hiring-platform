import asyncio
import uuid

from generation.constants.quality import QualityFlag
from generation.integrations import library, llm
from generation.repositories import key_checks
from generation.schemas.questions import AnswerItem, AnswerList
from generation.schemas.regenerate import QuestionContext, RegeneratedOption
from generation.schemas.verify import KeyCheck, QuestionQuality, ReportNote
from generation.services import verify as verify_service
from generation.services.verify import check_key, verify
from tests.unit.batch_fakes import run_batches

QUESTION_ID = uuid.uuid4()
TEXT = "A customer pays cash. Which entry is recorded?"


def context():
    return QuestionContext(
        set_id=uuid.uuid4(),
        kind="preparation",
        owner_id="ann",
        level="basic",
        topic="Bookkeeping",
        subtopics=[],
        existing=[TEXT],
    )


def question():
    # The key is on "Credit cash", but people pick "Debit cash".
    return QuestionQuality(
        text=TEXT,
        options=[
            RegeneratedOption(answer="Debit cash", correct=False),
            RegeneratedOption(answer="Credit cash", correct=True),
            RegeneratedOption(answer="Debit revenue", correct=False),
            RegeneratedOption(answer="Credit expenses", correct=False),
        ],
        answers=40,
        option_picks={"Debit cash": 30, "Credit cash": 6, "Debit revenue": 2, "Credit expenses": 2},
        reports=[ReportNote(reason="wrong_answer")],
    )


class FakeLLM:
    """Answers each call with the next of `results`, then the last one again."""

    def __init__(self, *results):
        self.results = list(results)
        self.prompts = []

    def with_structured_output(self, schema):
        return self

    async def ainvoke(self, messages):
        self.prompts.append("\n".join(message.content for message in messages))

        return self.results.pop(0) if len(self.results) > 1 else self.results[0]


def record(monkeypatch, verdict=None, flag=None, confirmation=None, quality=question):
    """Fakes the library and the models; the library's question (`quality`) carries `flag`."""
    calls = []

    async def fake_context(_question_id):
        return context()

    async def fake_quality(_question_id):
        return quality().model_copy(update={"flag": flag})

    async def fake_keep(question_id):
        calls.append(("keep", question_id))

    async def fake_replace(question_id, new):
        calls.append(("replace", new.text, [option.correct for option in new.options]))

    async def fake_regenerate(question_id, _context, reasons=None):
        calls.append(("regenerate", question_id))

    async def fake_rewrite(question_id, _context, text, reasons):
        calls.append(("rewrite", question_id))

    fake_llm = FakeLLM(verdict, *([confirmation] if confirmation else []))
    # Both checks list the options in their own order (the real order is a shuffle).
    monkeypatch.setattr(verify_service.random, "sample", lambda items, count: list(items))
    monkeypatch.setattr(verify_service, "option_order", lambda question_id, count: [*range(count)])
    monkeypatch.setattr(library, "get_question_context", fake_context)
    monkeypatch.setattr(library, "get_question_quality", fake_quality)
    monkeypatch.setattr(library, "keep_question", fake_keep)
    monkeypatch.setattr(library, "replace_question", fake_replace)
    monkeypatch.setattr(verify_service, "regenerate", fake_regenerate)
    # Nobody waits on a rewrite: it goes in the next batch (test_batch_questions.py).
    monkeypatch.setattr(verify_service.batch_work, "queue_rewrite", fake_rewrite)
    monkeypatch.setattr(llm, "get_verifier_llm", lambda: fake_llm)

    return calls, fake_llm


def test_a_wrong_key_is_moved_once_a_blind_second_check_agrees(monkeypatch):
    calls, fake_llm = record(
        monkeypatch, KeyCheck(correct_indexes=[0]), confirmation=KeyCheck(correct_indexes=[0])
    )

    asyncio.run(check_key(QUESTION_ID, question(), context()))

    assert calls == [("replace", TEXT, [True, False, False, False])]
    # No option is marked for the first check either, and how often each was picked never
    # reaches the model: the popular answer can be wrong.
    assert "0. Debit cash\n1. Credit cash\n" in fake_llm.prompts[0]
    assert "[correct]" not in fake_llm.prompts[0]
    assert "picked" not in fake_llm.prompts[0]
    # The second check marks no option.
    assert "marked" not in fake_llm.prompts[1]
    # The reason is counted; the reporter's own words never reach the model.
    assert "wrong_answer: 1" in fake_llm.prompts[0]
    assert "Cash comes in" not in fake_llm.prompts[0]


def test_a_key_the_second_check_doesnt_agree_on_replaces_the_question(monkeypatch):
    # The first check says "Debit cash", the blind one "Debit revenue": nothing moves the key,
    # so no future candidate is marked on an uncertain key.
    calls, _ = record(
        monkeypatch, KeyCheck(correct_indexes=[0]), confirmation=KeyCheck(correct_indexes=[2])
    )

    asyncio.run(check_key(QUESTION_ID, question(), context()))

    assert calls == [("rewrite", QUESTION_ID)]


def test_a_confirmed_key_keeps_the_question(monkeypatch):
    calls, _ = record(monkeypatch, KeyCheck(correct_indexes=[1]))

    asyncio.run(check_key(QUESTION_ID, question(), context()))

    assert calls == [("keep", QUESTION_ID)]


def test_a_question_without_one_right_option_is_replaced(monkeypatch):
    calls, _ = record(monkeypatch, KeyCheck(correct_indexes=None))

    asyncio.run(check_key(QUESTION_ID, question(), context()))

    assert calls == [("rewrite", QUESTION_ID)]


def test_a_wrong_key_waits_for_the_next_batch(monkeypatch):
    calls, fake_llm = record(monkeypatch, KeyCheck(correct_indexes=[1]), QualityFlag.WRONG_KEY)
    queued = []

    async def fake_add(session, question_id, text, marked):
        queued.append((question_id, text, marked))

    monkeypatch.setattr(key_checks, "add", fake_add)

    asyncio.run(verify(QUESTION_ID, QualityFlag.WRONG_KEY))

    # The key it's checked against is kept, so a result for a key moved since is dropped.
    assert queued == [(QUESTION_ID, TEXT, "Credit cash")]
    assert calls == []
    assert fake_llm.prompts == []


def test_a_flagged_rewrite_replaces_the_question(monkeypatch):
    calls, _ = record(monkeypatch, flag=QualityFlag.REWRITE)

    asyncio.run(verify(QUESTION_ID, QualityFlag.REWRITE))

    assert calls == [("rewrite", QUESTION_ID)]


def test_a_rewrite_hands_the_reported_reasons_to_the_new_question(monkeypatch):
    record(monkeypatch, flag=QualityFlag.REWRITE)
    handed = []

    async def fake_rewrite(question_id, _context, text, reasons):
        handed.append(reasons)

    monkeypatch.setattr(verify_service.batch_work, "queue_rewrite", fake_rewrite)

    asyncio.run(verify(QUESTION_ID, QualityFlag.REWRITE))

    assert handed == [["wrong_answer"]]


def test_weak_options_are_written_again_for_the_same_question_in_a_batch(monkeypatch):
    calls, _ = record(monkeypatch, flag=QualityFlag.WEAK_OPTIONS)
    answers = AnswerList(
        answers=[
            AnswerItem(
                id=0,
                correct_options=["Debit cash"],
                distractors=["Credit cash", "Debit capital", "Credit revenue"],
                ambiguous=False,
            )
        ]
    )

    asyncio.run(verify(QUESTION_ID, QualityFlag.WEAK_OPTIONS))
    run_batches(monkeypatch, lambda body: answers.model_dump_json())

    assert len(calls) == 1
    assert calls[0][:2] == ("replace", TEXT)
    assert sorted(calls[0][2]) == [False, False, False, True]


def test_a_question_kept_or_replaced_since_it_was_flagged_is_skipped(monkeypatch):
    calls, _ = record(monkeypatch, flag=None)

    asyncio.run(verify(QUESTION_ID, QualityFlag.REWRITE))

    assert calls == []


def test_the_librarys_current_flag_wins_over_the_one_sent(monkeypatch):
    calls, _ = record(monkeypatch, flag=QualityFlag.REWRITE)

    asyncio.run(verify(QUESTION_ID, QualityFlag.WRONG_KEY))

    assert calls == [("rewrite", QUESTION_ID)]


def test_a_deleted_question_is_skipped(monkeypatch):
    calls, _ = record(monkeypatch)

    async def gone(_question_id):
        return None

    monkeypatch.setattr(library, "get_question_quality", gone)

    asyncio.run(verify(QUESTION_ID, QualityFlag.REWRITE))

    assert calls == []


def test_the_key_checks_order_hides_the_marked_option_and_holds_for_a_question():
    orders = [verify_service.option_order(uuid.uuid4(), 4) for _ in range(200)]

    # Every option shows up first sometimes: the first position says nothing about the key.
    assert {order[0] for order in orders} == {0, 1, 2, 3}
    assert all(sorted(order) == [0, 1, 2, 3] for order in orders)
    # A batched check's reply is read in the order it was asked in.
    assert verify_service.option_order(QUESTION_ID, 4) == verify_service.option_order(
        QUESTION_ID, 4
    )
