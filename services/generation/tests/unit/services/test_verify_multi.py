import asyncio

import pytest

from generation.constants.quality import QualityFlag
from generation.prompts.answers import MULTI_ANSWER_KIND
from generation.prompts.checker import MULTI_ANSWER_KEY, SINGLE_ANSWER_KEY
from generation.repositories import key_checks
from generation.schemas.questions import AnswerItem, AnswerList
from generation.schemas.regenerate import RegeneratedOption
from generation.schemas.verify import KeyCheck, QuestionQuality
from generation.services.verify import check_key, verify
from tests.unit.batch_fakes import run_batches
from tests.unit.services.test_verify import QUESTION_ID, context, question, record

TEXT = "A shop sells goods for cash. Which entries are recorded?"


def multi_answer():
    # The key marks "Debit cash" and "Credit cash"; the entries are "Debit cash" and "Credit
    # revenue". The tests list the options in their own order (record()).
    return QuestionQuality(
        text=TEXT,
        options=[
            RegeneratedOption(answer="Debit cash", correct=True),
            RegeneratedOption(answer="Credit revenue", correct=False),
            RegeneratedOption(answer="Debit revenue", correct=False),
            RegeneratedOption(answer="Credit cash", correct=True),
        ],
        answers=40,
        option_picks={"Debit cash": 35, "Credit revenue": 30, "Debit revenue": 2, "Credit cash": 4},
        reports=[],
    )


def checked(monkeypatch, verdict, confirmation=None):
    calls, fake_llm = record(
        monkeypatch,
        KeyCheck(correct_indexes=verdict),
        confirmation=confirmation,
        quality=multi_answer,
    )
    asyncio.run(check_key(QUESTION_ID, multi_answer(), context()))

    return calls, fake_llm


def test_a_confirmed_set_of_right_options_keeps_the_question(monkeypatch):
    calls, fake_llm = checked(monkeypatch, [3, 0])

    assert calls == [("keep", QUESTION_ID)]
    assert MULTI_ANSWER_KEY in fake_llm.prompts[0]


def test_a_wrong_set_is_moved_once_a_blind_second_check_names_the_same_set(monkeypatch):
    calls, fake_llm = checked(monkeypatch, [0, 1], KeyCheck(correct_indexes=[1, 0]))

    assert calls == [("replace", TEXT, [True, True, False, False])]
    assert MULTI_ANSWER_KEY in fake_llm.prompts[1]


def test_a_set_the_second_check_doesnt_name_replaces_the_question(monkeypatch):
    calls, _ = checked(monkeypatch, [0, 2], KeyCheck(correct_indexes=[0, 1, 2]))

    assert calls == [("rewrite", QUESTION_ID)]


@pytest.mark.parametrize("verdict", [[2], [0, 1, 2, 3], [0, 7]])
def test_a_key_of_the_other_kind_every_option_or_one_not_there_replaces_it(monkeypatch, verdict):
    calls, _ = checked(monkeypatch, verdict)

    assert calls == [("rewrite", QUESTION_ID)]


def test_a_single_answer_question_checked_with_several_right_is_replaced(monkeypatch):
    calls, fake_llm = record(monkeypatch, KeyCheck(correct_indexes=[0, 1]))

    asyncio.run(check_key(QUESTION_ID, question(), context()))

    assert calls == [("rewrite", QUESTION_ID)]
    assert SINGLE_ANSWER_KEY in fake_llm.prompts[0]


def test_a_wrong_set_waits_for_the_next_batch_with_every_marked_option(monkeypatch):
    record(monkeypatch, flag=QualityFlag.WRONG_KEY, quality=multi_answer)
    queued = []

    async def fake_add(question_id, text, marked):
        queued.append((question_id, text, marked))

    monkeypatch.setattr(key_checks, "add", fake_add)

    asyncio.run(verify(QUESTION_ID, QualityFlag.WRONG_KEY))

    assert queued == [(QUESTION_ID, TEXT, "Debit cash\nCredit cash")]


def test_new_options_for_a_multi_answer_question_keep_its_kind(monkeypatch):
    calls, _ = record(monkeypatch, flag=QualityFlag.WEAK_OPTIONS, quality=multi_answer)
    answers = AnswerList(
        answers=[
            AnswerItem(
                id=0,
                correct_options=["Debit cash", "Credit revenue"],
                distractors=["Credit cash", "Debit capital"],
                ambiguous=False,
            )
        ]
    )

    asyncio.run(verify(QUESTION_ID, QualityFlag.WEAK_OPTIONS))
    batches = run_batches(monkeypatch, lambda body: answers.model_dump_json())

    assert calls[0][:2] == ("replace", TEXT)
    assert sorted(calls[0][2]) == [False, False, True, True]
    [sent] = batches.sent.values()
    [body] = sent.values()
    assert MULTI_ANSWER_KIND in body["messages"][0]["content"]
