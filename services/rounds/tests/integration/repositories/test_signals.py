import os
import uuid

from testee_common.db.lock_waits import hold_first_commit, race

from rounds.repositories import sessions, signals
from rounds.services import invite_scores
from tests.integration import transactions
from tests.integration.factories import MOST_SIGNALS, created, topic
from tests.integration.transactions import transaction


def test_signals_are_saved_with_their_question_and_loaded_for_the_scorecard(run):
    invite_id = uuid.uuid4()

    async def scenario():
        [row] = await created("cand", invite_id, [topic()], 60, company_id=uuid.uuid4())
        question_id = uuid.UUID(row.questions[0]["id"])
        await transaction(signals.add_signal, row.id, question_id, "tab_leave", MOST_SIGNALS)
        await transaction(signals.add_signal, row.id, None, "copy", MOST_SIGNALS)

        return await transaction(sessions.list_for_invite, invite_id, signals=True), question_id

    [row], question_id = run(scenario())

    assert sorted((signal.kind, signal.question_id) for signal in row.signals) == [
        ("copy", None),
        ("tab_leave", question_id),
    ]


def test_a_returns_length_times_the_latest_leave_and_a_short_one_isnt_counted(run):
    invite_id = uuid.uuid4()

    async def scenario():
        [row] = await created("cand", invite_id, [topic(2)], 60, company_id=uuid.uuid4())
        await transaction(signals.add_signal, row.id, None, "tab_leave", MOST_SIGNALS)
        await transaction(signals.set_away, row.id, 5)
        await transaction(signals.add_signal, row.id, None, "tab_leave", MOST_SIGNALS)
        # A moment's leave: kept, not counted.
        await transaction(signals.set_away, row.id, 0.5)
        # A return without a leave left open changes nothing.
        await transaction(signals.set_away, row.id, 9)
        # A leave never returned from counts.
        await transaction(signals.add_signal, row.id, None, "tab_leave", MOST_SIGNALS)
        [found] = await transaction(sessions.list_for_invite, invite_id, signals=True)

        return found, await invite_scores.scores([invite_id])

    found, scores = run(scenario())

    assert sorted(signal.away_seconds or -1 for signal in found.signals) == [-1, 0.5, 5]
    assert scores[invite_id]["tab_leaves"] == 2


def test_signals_sent_at_once_still_stop_at_the_limit(run, monkeypatch):
    invite_id = uuid.uuid4()
    most = MOST_SIGNALS

    async def scenario():
        [row] = await created("cand", invite_id, [topic()], 30, company_id=uuid.uuid4())
        question_id = uuid.UUID(row.questions[0]["id"])

        for _ in range(most - 1):
            await transaction(signals.add_signal, row.id, question_id, "tab_leave", MOST_SIGNALS)

        # The last place: the second waits on the question's lock until the first commits.
        held = hold_first_commit(monkeypatch, transactions)
        await race(
            os.environ["DATABASE_URL"],
            held,
            *(
                transaction(signals.add_signal, row.id, question_id, "tab_leave", most)
                for _ in range(2)
            ),
        )
        [found] = await transaction(sessions.list_for_invite, invite_id, signals=True)

        return len(found.signals)

    assert run(scenario()) == most
