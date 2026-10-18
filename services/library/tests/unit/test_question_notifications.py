import asyncio
import uuid
from types import SimpleNamespace

import pytest
from prepza_common.notifications import NOTIFICATION_REQUESTED

from app.constants.quality import QualityFlag
from app.integrations import generation
from app.services import outbox
from app.services.quality import review
from app.storage import preparations, quality

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

    async def fake_load(_question_id):
        return question, stats, {"wrong_answer": 2}, 0, 0

    async def fake_verify(question_id, flag):
        pass

    async def fake_change(question_id, previous, flag, notice=None):
        saved.append(notice)

        return True

    async def fake_set(_question_id):
        return question_set

    async def fake_topic(_question_id):
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


def test_a_flagged_question_is_not_notified_again(monkeypatch):
    saved, flushes = run_review(monkeypatch, QualityFlag.REWRITE, kit())

    assert saved == [None]
    assert flushes == []


def fake_session(monkeypatch, flag, archived=None):
    added = []
    # What the session's lookups find, in order: the question's flag, its set and its topic.
    replies = [flag, kit(), TOPIC]

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def scalar(self, statement):
            return replies.pop(0)

        async def scalars(self, statement):
            # The question has no copies in companies' tests.
            return []

        async def execute(self, statement):
            pass

        def add(self, row):
            added.append(row)

        async def commit(self):
            pass

    async def fake_archive(session, question_id, fixed=False):
        if archived is not None:
            archived.append(fixed)

    monkeypatch.setattr(preparations, "Session", FakeSession)
    monkeypatch.setattr(quality, "archive", fake_archive)

    return added


def test_fixing_a_flagged_question_notifies_its_owner(monkeypatch):
    added = fake_session(monkeypatch, QualityFlag.WRONG_KEY)

    asyncio.run(preparations.replace_question(QUESTION_ID, "What is debit?", OPTIONS))

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
        )
    ]


def test_replacing_an_unflagged_question_notifies_nobody(monkeypatch):
    added = fake_session(monkeypatch, None)

    asyncio.run(preparations.replace_question(QUESTION_ID, "What is debit?", OPTIONS))

    assert added == []


@pytest.mark.parametrize("flag, fixed", [(QualityFlag.WRONG_KEY, True), (None, False)])
def test_only_a_flagged_questions_revision_counts_as_fixed(monkeypatch, flag, fixed):
    archived = []
    fake_session(monkeypatch, flag, archived)

    asyncio.run(preparations.replace_question(QUESTION_ID, "What is debit?", OPTIONS))

    assert archived == [fixed]
