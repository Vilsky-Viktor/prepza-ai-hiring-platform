import os
import uuid

import pytest
from prepza_common.limit_list import LIMITS, LIMITS_KEY
from prepza_common.lock_waits import hold_first_commit, race

from app.integrations.redis import get_redis
from app.storage import sessions, signals
from tests.integration.factories import topic


def test_signals_are_saved_with_their_question_and_loaded_for_the_scorecard(run):
    invite_id = uuid.uuid4()

    async def scenario():
        [row] = await sessions.create_many(
            "cand", invite_id, [topic()], 60, company_id=uuid.uuid4()
        )
        question_id = uuid.UUID(row.questions[0]["id"])
        await signals.add_signal(row.id, question_id, "tab_leave")
        await signals.add_signal(row.id, None, "copy")

        return await sessions.list_for_invite(invite_id, signals=True), question_id

    [row], question_id = run(scenario())

    assert sorted((signal.kind, signal.question_id) for signal in row.signals) == [
        ("copy", None),
        ("tab_leave", question_id),
    ]


@pytest.mark.parametrize("edited", [None, 3])
def test_a_question_keeps_a_limited_number_of_signals(run, edited):
    """As many as the limit's edited value, or its default when it isn't edited."""
    invite_id = uuid.uuid4()
    most = edited or LIMITS["MAX_SIGNALS_PER_QUESTION"].default

    async def scenario():
        if edited:
            await get_redis().hset(LIMITS_KEY, "MAX_SIGNALS_PER_QUESTION", edited)

        try:
            [row] = await sessions.create_many(
                "cand", invite_id, [topic()], 30, company_id=uuid.uuid4()
            )
            question_id = uuid.UUID(row.questions[0]["id"])

            for _ in range(most + 5):
                await signals.add_signal(row.id, question_id, "tab_leave")

            await signals.add_signal(row.id, None, "copy")
            [found] = await sessions.list_for_invite(invite_id, signals=True)
        finally:
            await get_redis().hdel(LIMITS_KEY, "MAX_SIGNALS_PER_QUESTION")

        return found

    found = run(scenario())

    on_question = [signal for signal in found.signals if signal.question_id is not None]
    assert len(on_question) == most
    # Another question (here, none on screen) still keeps its own.
    assert len(found.signals) == most + 1


def test_a_returns_length_times_the_latest_leave_and_a_short_one_isnt_counted(run):
    invite_id = uuid.uuid4()

    async def scenario():
        [row] = await sessions.create_many(
            "cand", invite_id, [topic(2)], 60, company_id=uuid.uuid4()
        )
        await signals.add_signal(row.id, None, "tab_leave")
        await signals.set_away(row.id, 5)
        await signals.add_signal(row.id, None, "tab_leave")
        # A moment's leave: kept, not counted.
        await signals.set_away(row.id, 0.5)
        # A return without a leave left open changes nothing.
        await signals.set_away(row.id, 9)
        # A leave never returned from counts.
        await signals.add_signal(row.id, None, "tab_leave")
        [found] = await sessions.list_for_invite(invite_id, signals=True)

        return found, await sessions.scores_for_invites([invite_id])

    found, scores = run(scenario())

    assert sorted(signal.away_seconds or -1 for signal in found.signals) == [-1, 0.5, 5]
    assert scores[invite_id]["tab_leaves"] == 2


def test_signals_sent_at_once_still_stop_at_the_limit(run, monkeypatch):
    invite_id = uuid.uuid4()
    most = LIMITS["MAX_SIGNALS_PER_QUESTION"].default

    async def scenario():
        [row] = await sessions.create_many(
            "cand", invite_id, [topic()], 30, company_id=uuid.uuid4()
        )
        question_id = uuid.UUID(row.questions[0]["id"])

        for _ in range(most - 1):
            await signals.add_signal(row.id, question_id, "tab_leave")

        # The last place: the second waits on the question's lock until the first commits.
        held = hold_first_commit(monkeypatch, signals, "Db")
        await race(
            os.environ["DATABASE_URL"],
            held,
            *(signals.add_signal(row.id, question_id, "tab_leave") for _ in range(2)),
        )
        [found] = await sessions.list_for_invite(invite_id, signals=True)

        return len(found.signals)

    assert run(scenario()) == most
