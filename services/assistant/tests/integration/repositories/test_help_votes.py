"""Votes on the help chat's answers in the real database: one row an answer, changed in place
and deleted when cleared; nothing but the answer's id, its trace and the vote."""

import uuid

from sqlalchemy import inspect, select

from assistant.core.db import Session, engine
from assistant.models.help_votes import HelpVote
from assistant.repositories import help_votes
from tests.integration.transactions import transaction


async def row(answer_id):
    async with Session() as session:
        return await session.scalar(select(HelpVote).where(HelpVote.answer_id == answer_id))


def test_a_vote_is_kept_changed_in_place_and_deleted_when_cleared(run):
    answer_id, trace_id = uuid.uuid4(), "a" * 32

    async def scenario():
        await transaction(help_votes.save, answer_id, trace_id, 1)
        first = await row(answer_id)
        await transaction(help_votes.save, answer_id, trace_id, -1)
        changed = await row(answer_id)
        current = await transaction(help_votes.vote_of, answer_id)
        await transaction(help_votes.save, answer_id, trace_id, None)

        return (
            first,
            changed,
            current,
            await row(answer_id),
            await transaction(help_votes.vote_of, answer_id),
        )

    first, changed, current, cleared, after = run(scenario())

    assert (first.vote, first.trace_id) == (1, trace_id)
    assert (changed.vote, changed.trace_id, changed.created_at) == (-1, trace_id, first.created_at)
    assert changed.updated_at >= first.updated_at
    assert current == -1
    assert (cleared, after) == (None, None)


def test_clearing_a_vote_never_given_changes_nothing(run):
    answer_id = uuid.uuid4()

    async def scenario():
        await transaction(help_votes.save, answer_id, None, None)

        return await row(answer_id)

    assert run(scenario()) is None


def test_the_table_holds_no_text_and_no_voter(run):
    async def columns():
        async with engine.connect() as connection:
            return await connection.run_sync(
                lambda sync: [c["name"] for c in inspect(sync).get_columns("help_votes")]
            )

    assert sorted(run(columns())) == ["answer_id", "created_at", "trace_id", "updated_at", "vote"]


def test_answers_voted_down_are_found_by_their_id_and_trace_only(run):
    down, up = uuid.uuid4(), uuid.uuid4()

    async def scenario():
        await transaction(help_votes.save, down, "c" * 32, -1)
        await transaction(help_votes.save, up, "d" * 32, 1)
        found = await transaction(help_votes.voted_down)

        for answer_id in (down, up):
            await transaction(help_votes.save, answer_id, None, None)

        return found

    mine = [(v.answer_id, v.trace_id) for v in run(scenario()) if v.answer_id in (down, up)]

    assert mine == [(down, "c" * 32)]
