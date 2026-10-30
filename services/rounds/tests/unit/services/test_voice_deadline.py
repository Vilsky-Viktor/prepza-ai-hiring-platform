import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fake_redis import DownRedis

from rounds.constants.rounds import TIME_GRACE_SECONDS
from rounds.constants.voice import IN_TIME_KEY, VOICE_ANSWER_GRACE_SECONDS, VOICE_UPLOAD_SECONDS
from rounds.models.sessions import Session
from rounds.services import voice_deadline

QUESTION_ID = uuid4()


def shown(seconds_ago: float, seconds: int | None = 30) -> Session:
    """A voice section whose question (of `seconds`, None untimed) was shown this long ago."""
    return Session(
        id=uuid4(),
        user_id="cand",
        status="in_progress",
        questions=[{"id": str(QUESTION_ID), "text": "Q?", "options": [], "seconds": seconds}],
        question_shown_at=datetime.now(UTC) - timedelta(seconds=seconds_ago),
        answers=[],
    )


def grace_after(row: Session) -> int:
    asyncio.run(voice_deadline.note_arrival(row, QUESTION_ID))

    return asyncio.run(voice_deadline.answer_grace(row.id, QUESTION_ID))


@pytest.mark.parametrize(
    ("seconds_ago", "grace"),
    [
        # Well before the deadline, and just after it, while the recording may still upload.
        (10, VOICE_ANSWER_GRACE_SECONDS),
        (30 + VOICE_UPLOAD_SECONDS - 0.5, VOICE_ANSWER_GRACE_SECONDS),
        # Past the upload's margin: the usual grace.
        (30 + VOICE_UPLOAD_SECONDS + 1, TIME_GRACE_SECONDS),
    ],
)
def test_a_spoken_answer_received_in_time_counts_a_little_past_the_deadline(
    redis, seconds_ago, grace
):
    row = shown(seconds_ago)

    assert grace_after(row) == grace


def test_the_note_lasts_until_the_grace_ends(redis):
    row = shown(10)
    grace_after(row)

    ttl = redis.expiries[IN_TIME_KEY.format(session_id=row.id)]
    assert 20 + VOICE_ANSWER_GRACE_SECONDS - 1 <= ttl <= 20 + VOICE_ANSWER_GRACE_SECONDS + 1


def test_only_the_question_heard_gets_the_longer_grace(redis):
    row = shown(10)
    asyncio.run(voice_deadline.note_arrival(row, QUESTION_ID))

    assert asyncio.run(voice_deadline.answer_grace(row.id, uuid4())) == TIME_GRACE_SECONDS
    assert asyncio.run(voice_deadline.answer_grace(uuid4(), QUESTION_ID)) == TIME_GRACE_SECONDS


def test_an_untimed_question_needs_no_note(redis):
    row = shown(10, seconds=None)

    assert grace_after(row) == TIME_GRACE_SECONDS
    assert redis.counts == {}


def test_without_redis_the_usual_grace_holds(monkeypatch):
    monkeypatch.setattr(voice_deadline, "get_redis", lambda: DownRedis())

    assert grace_after(shown(10)) == TIME_GRACE_SECONDS
