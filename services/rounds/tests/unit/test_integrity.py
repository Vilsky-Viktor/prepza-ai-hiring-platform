import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from prepza_common.auth import current_user
from prepza_common.constants import RATE_LIMITED
from prepza_common.limit_list import LIMITS
from prepza_common.user import User

from app.helpers.review import add_signals, build_review
from app.main import app
from app.models.answers import Answer
from app.models.sessions import Session
from app.models.signals import Signal
from app.routers import sessions as routes
from app.schemas.library import TopicQuestions
from app.storage import sessions, signals

QUESTION_ID = uuid4()


def session(seconds):
    return Session(
        id=uuid4(),
        user_id="cand",
        topic_id=uuid4(),
        interview_set_id=uuid4(),
        candidate_invite_id=uuid4(),
        topic_title="Python",
        status="in_progress",
        questions=[
            {
                "id": str(QUESTION_ID),
                "text": "Q?",
                "options": [{"answer": "A", "correct": True}, {"answer": "B", "correct": False}],
            }
        ],
        final_score=None,
        started_at=datetime.now(UTC),
        finished_at=None,
        question_seconds=None,
        question_shown_at=None,
        answers=[
            Answer(
                id=uuid4(),
                question_id=QUESTION_ID,
                option_index=0,
                correct=True,
                score=100,
                seconds=seconds,
                timed_out=False,
            )
        ],
    )


def test_answers_under_three_seconds_are_fast():
    assert build_review(session(seconds=2))[0].answer.fast
    assert not build_review(session(seconds=3))[0].answer.fast


def test_each_candidate_gets_their_own_option_order(monkeypatch):
    class FakeDb:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        def add_all(self, rows):
            pass

        async def commit(self):
            pass

    monkeypatch.setattr(sessions, "Db", FakeDb)
    options = [{"answer": str(i), "correct": i == 0} for i in range(4)]
    topic = TopicQuestions.model_validate(
        {
            "id": str(uuid4()),
            "preparation_id": str(uuid4()),
            "title": "T",
            "questions": [{"id": str(uuid4()), "text": "Q?", "options": options}],
        }
    )
    orders = set()

    for _ in range(30):
        rows = asyncio.run(sessions.create_many("cand", uuid4(), [topic], 60))
        question = rows[0].questions[0]
        orders.add(tuple(option["answer"] for option in question["options"]))
        assert [option["answer"] for option in question["options"] if option["correct"]] == ["0"]

    assert len(orders) > 1


@pytest.mark.parametrize("edited", [None, 5])
def test_the_browser_reports_signals(monkeypatch, redis, published, edited):
    row = session(seconds=10)
    row.answers = []
    row.question_shown_at = datetime.now(UTC)
    counted = []

    async def fake_get(session_id):
        return row

    async def fake_add_signal(session_id, question_id, kind):
        counted.append((question_id, kind))

    # At the limit's edited value, or its default when it isn't edited.
    allowed = edited or LIMITS["SIGNALS_PER_MINUTE"].default

    if edited:
        redis.limits["SIGNALS_PER_MINUTE"] = edited

    monkeypatch.setattr(sessions, "get", fake_get)
    monkeypatch.setattr(signals, "add_signal", fake_add_signal)
    app.dependency_overrides[current_user] = lambda: User(
        uid="cand", email="cand@example.com", email_verified=True
    )

    try:
        client = TestClient(app)
        ok = client.post(f"/sessions/{row.id}/signals", json={"kind": "tab_leave"})
        bad = client.post(f"/sessions/{row.id}/signals", json={"kind": "other"})

        # A browser (or a script) reporting too often in a minute is refused, and saves nothing.
        for _ in range(allowed - 1):
            client.post(f"/sessions/{row.id}/signals", json={"kind": "copy"})

        flooded = client.post(f"/sessions/{row.id}/signals", json={"kind": "copy"})
    finally:
        app.dependency_overrides.clear()

    assert ok.status_code == 204
    assert bad.status_code == 422
    assert counted[0] == (QUESTION_ID, "tab_leave")
    assert flooded.status_code == 429
    assert flooded.json()["detail"] == RATE_LIMITED
    assert len(counted) == allowed
    assert [(data["limit"], data["user_id"]) for _, data in published] == [
        ("SIGNALS_PER_MINUTE", "cand")
    ]


def test_with_redis_down_a_signal_is_still_saved(monkeypatch):
    row = session(seconds=10)
    row.answers = []
    row.question_shown_at = datetime.now(UTC)
    counted = []

    class DownRedis:
        def pipeline(self, transaction):
            raise ConnectionError("Redis is down")

        async def hgetall(self, key):
            raise ConnectionError("Redis is down")

    async def fake_get(session_id):
        return row

    async def fake_add_signal(session_id, question_id, kind):
        counted.append((question_id, kind))

    monkeypatch.setattr(sessions, "get", fake_get)
    monkeypatch.setattr(signals, "add_signal", fake_add_signal)
    monkeypatch.setattr(routes, "get_redis", DownRedis)
    app.dependency_overrides[current_user] = lambda: User(
        uid="cand", email="cand@example.com", email_verified=True
    )

    try:
        saved = TestClient(app).post(f"/sessions/{row.id}/signals", json={"kind": "copy"})
    finally:
        app.dependency_overrides.clear()

    assert saved.status_code == 204
    assert counted == [(QUESTION_ID, "copy")]


def test_signals_are_counted_on_their_question():
    items = build_review(session(seconds=10))
    signals = [
        Signal(question_id=QUESTION_ID, kind="tab_leave"),
        Signal(question_id=QUESTION_ID, kind="tab_leave"),
        Signal(question_id=QUESTION_ID, kind="copy"),
        Signal(question_id=None, kind="tab_leave"),
    ]

    add_signals(items, signals)

    assert (items[0].tab_leaves, items[0].copies) == (2, 1)


def test_a_page_leave_counts_only_when_it_lasted_two_seconds_or_never_ended():
    items = build_review(session(seconds=10))
    signals = [
        # A notification or a permission prompt taking focus for a moment.
        Signal(question_id=QUESTION_ID, kind="tab_leave", away_seconds=0.4),
        Signal(question_id=QUESTION_ID, kind="tab_leave", away_seconds=2),
        # Never came back (or a browser that doesn't say).
        Signal(question_id=QUESTION_ID, kind="tab_leave", away_seconds=None),
    ]

    add_signals(items, signals)

    assert items[0].tab_leaves == 2


def test_coming_back_records_how_long_the_leave_lasted(monkeypatch):
    row = session(seconds=10)
    row.answers = []
    row.question_shown_at = datetime.now(UTC)
    calls = []

    async def fake_get(session_id):
        return row

    async def fake_add_signal(session_id, question_id, kind):
        calls.append(("signal", kind))

    async def fake_set_away(session_id, seconds):
        calls.append(("away", seconds))

    monkeypatch.setattr(sessions, "get", fake_get)
    monkeypatch.setattr(signals, "add_signal", fake_add_signal)
    monkeypatch.setattr(signals, "set_away", fake_set_away)
    app.dependency_overrides[current_user] = lambda: User(
        uid="cand", email="cand@example.com", email_verified=True
    )

    try:
        client = TestClient(app)
        back = client.post(
            f"/sessions/{row.id}/signals", json={"kind": "tab_return", "seconds": 1.5}
        )
        negative = client.post(
            f"/sessions/{row.id}/signals", json={"kind": "tab_return", "seconds": -1}
        )
    finally:
        app.dependency_overrides.clear()

    assert back.status_code == 204
    assert negative.status_code == 422
    # A return is no signal of its own: it only times the leave.
    assert calls == [("away", 1.5)]


@pytest.mark.parametrize("kind", ["practice", "preview"])
def test_a_practice_round_or_a_preview_records_no_signals(monkeypatch, kind):
    """No one assesses them, so nothing about leaving the page or copying is kept."""
    row = session(seconds=10)
    row.answers = []
    row.question_shown_at = datetime.now(UTC)
    setattr(row, kind, True)
    counted = []

    async def fake_get(session_id):
        return row

    async def fake_add_signal(session_id, question_id, kind):
        counted.append(kind)

    async def fake_set_away(session_id, seconds):
        counted.append("away")

    monkeypatch.setattr(sessions, "get", fake_get)
    monkeypatch.setattr(signals, "add_signal", fake_add_signal)
    monkeypatch.setattr(signals, "set_away", fake_set_away)
    app.dependency_overrides[current_user] = lambda: User(
        uid="cand", email="cand@example.com", email_verified=True
    )

    try:
        client = TestClient(app)
        leave = client.post(f"/sessions/{row.id}/signals", json={"kind": "tab_leave"})
        back = client.post(f"/sessions/{row.id}/signals", json={"kind": "tab_return", "seconds": 3})
    finally:
        app.dependency_overrides.clear()

    assert (leave.status_code, back.status_code) == (204, 204)
    assert counted == []
