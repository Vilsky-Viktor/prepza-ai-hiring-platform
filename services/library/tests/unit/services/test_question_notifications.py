import asyncio
import uuid
from types import SimpleNamespace

import pytest
from testee_common.events.notifications import NOTIFICATION_REQUESTED

from library.constants.events import QUESTION_FIXED
from library.constants.quality import QualityFlag
from library.integrations import generation
from library.repositories import preparations, quality
from library.services import outbox, questions
from library.services.quality import review

QUESTION_ID = uuid.uuid4()
SET_ID = uuid.uuid4()
OPTIONS = [
    {"answer": "Debit cash", "correct": True},
    {"answer": "Credit cash", "correct": False},
]
TOPIC = "Double-entry bookkeeping"


def kit(owner_type="company", owner_id="u1"):
    return SimpleNamespace(id=SET_ID, owner_type=owner_type, owner_id=owner_id, title="Accounting")


def run_review(monkeypatch, previous_flag, question_set):
    """Reviews a question with two wrong-answer reports; returns saved notices and flushes."""
    saved, flushes = [], []
    question = SimpleNamespace(text="Which entry records a sale?", options=OPTIONS)
    stats = SimpleNamespace(
        strong_answers=0,
        strong_correct=0,
        weak_answers=0,
        weak_correct=0,
        timeouts=0,
        answers=0,
        correct=0,
        option_picks={},
        flag=previous_flag,
        kept=False,
    )

    async def fake_load(session, _question_id):
        return question, stats, {"wrong_answer": 2}, 0, 0

    async def fake_verify(question_id, flag):
        pass

    async def fake_change(session, question_id, previous, flag, notice=None):
        saved.append(notice)

        return True

    async def fake_set(session, _question_id):
        return question_set

    async def fake_topic(session, _question_id):
        return TOPIC

    async def fake_flush():
        flushes.append(True)

    monkeypatch.setattr(quality, "load", fake_load)
    monkeypatch.setattr(generation, "verify_question", fake_verify)
    monkeypatch.setattr(quality, "change_flag", fake_change)
    monkeypatch.setattr(preparations, "get_for_question", fake_set)
    monkeypatch.setattr(preparations, "topic_of_question", fake_topic)
    monkeypatch.setattr(outbox, "flush_quietly", fake_flush)

    asyncio.run(review(QUESTION_ID))

    return saved, flushes


def test_a_newly_flagged_interview_question_notifies_the_company(monkeypatch):
    saved, _ = run_review(monkeypatch, None, kit("company", "c1"))

    assert saved[0]["recipient"] == "company"
    assert saved[0]["recipient_id"] == "c1"
    assert saved[0]["link"] == "/companies/c1/interviews"


def test_a_newly_flagged_template_question_notifies_no_company(monkeypatch):
    saved, flushes = run_review(monkeypatch, None, kit("platform", "testee"))

    assert saved == [None]
    assert flushes == []


def test_a_flagged_question_is_not_notified_again(monkeypatch):
    saved, flushes = run_review(monkeypatch, QualityFlag.REWRITE, kit())

    assert saved == [None]
    assert flushes == []


def fake_session(monkeypatch, flag, archived=None, question_set=None):
    """Replaces the question with every repository faked; the rows added to the transaction."""
    added = []

    class FakeSession:
        @classmethod
        def begin(cls):
            return cls()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        def add(self, row):
            added.append(row)

    async def current_flag(session, question_id):
        return flag

    async def question(session, question_id):
        # The question's content before it's replaced.
        return SimpleNamespace(text="What is a debit?", options=OPTIONS)

    async def set_content(session, question_id, text, options):
        pass

    async def fake_set(session, question_id):
        return question_set or kit()

    async def fake_topic(session, question_id):
        return TOPIC

    async def fake_archive(session, question_id, fixed=False):
        if archived is not None:
            archived.append(fixed)

    async def no_flush():
        pass

    monkeypatch.setattr(questions, "Session", FakeSession)
    monkeypatch.setattr(quality, "current_flag", current_flag)
    monkeypatch.setattr(preparations, "question", question)
    monkeypatch.setattr(preparations, "set_content", set_content)
    monkeypatch.setattr(preparations, "get_for_question", fake_set)
    monkeypatch.setattr(preparations, "topic_of_question", fake_topic)
    monkeypatch.setattr(quality, "archive", fake_archive)
    monkeypatch.setattr(outbox, "flush_quietly", no_flush)

    return added


def test_fixing_a_flagged_question_notifies_its_owner(monkeypatch):
    added = fake_session(monkeypatch, QualityFlag.WRONG_KEY)

    asyncio.run(questions.replace(QUESTION_ID, "What is debit?", OPTIONS))

    assert [(row.event_type, row.data) for row in added] == [
        (
            NOTIFICATION_REQUESTED,
            {
                "recipient": "company",
                "recipient_id": "u1",
                "kind": "question_fixed",
                "link": "/companies/u1/interviews",
                "data": {"title": "Accounting", "topic": TOPIC},
            },
        ),
        # Its copies in companies' tests are fixed after it, from their old content.
        (
            QUESTION_FIXED,
            {"question_id": str(QUESTION_ID), "text": "What is a debit?", "options": OPTIONS},
        ),
    ]


def test_fixing_a_flagged_template_question_notifies_no_company(monkeypatch):
    added = fake_session(monkeypatch, QualityFlag.WRONG_KEY, question_set=kit("platform", "testee"))

    asyncio.run(questions.replace(QUESTION_ID, "What is debit?", OPTIONS))

    # Only its copies in companies' tests are fixed after it, and those companies told then.
    assert [row.event_type for row in added] == [QUESTION_FIXED]


def test_replacing_an_unflagged_question_notifies_nobody(monkeypatch):
    added = fake_session(monkeypatch, None)

    asyncio.run(questions.replace(QUESTION_ID, "What is debit?", OPTIONS))

    assert added == []


@pytest.mark.parametrize("flag, fixed", [(QualityFlag.WRONG_KEY, True), (None, False)])
def test_only_a_flagged_questions_revision_counts_as_fixed(monkeypatch, flag, fixed):
    archived = []
    fake_session(monkeypatch, flag, archived)

    asyncio.run(questions.replace(QUESTION_ID, "What is debit?", OPTIONS))

    assert archived == [fixed]
