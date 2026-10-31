"""An interview's notes in the database: one pinned at a time, even when two are pinned at once;
each interview's count and pinned note in its list; gone with the interview and the company; in
their author's data download."""

import os
import uuid

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from testee_common.db.lock_waits import hold_first_commit, race

from companies.core.db import Session
from companies.models.interview_notes import InterviewNote
from companies.repositories import accounts, interview_notes, interviews
from companies.services.interview_views import interviews_page
from tests.integration import factories, transactions
from tests.integration.transactions import transaction


async def note(team, role: str, text: str):
    """A note written by `role`'s membership."""
    _, _, member = await factories.as_member(getattr(team, role), team.interview.id)

    return await transaction(interview_notes.add, team.interview, member.id, None, text)


async def pinned(interview_id) -> list[str]:
    async with Session() as session:
        return list(
            await session.scalars(
                select(InterviewNote.text).where(
                    InterviewNote.interview_id == interview_id, InterviewNote.pinned
                )
            )
        )


async def note_count(**where) -> int:
    conditions = [getattr(InterviewNote, name) == value for name, value in where.items()]

    async with Session() as session:
        return await session.scalar(
            select(func.count()).select_from(InterviewNote).where(*conditions)
        )


def test_two_pins_at_once_take_turns_and_leave_one_pinned(run, monkeypatch):
    """The second waits on the interview's row lock until the first commits, then unpins it."""

    async def scenario():
        team = await factories.team("race")
        first = await note(team, "owner", "First")
        second = await note(team, "admin", "Second")
        held = hold_first_commit(monkeypatch, transactions)
        both = await race(
            os.environ["DATABASE_URL"],
            held,
            transaction(interview_notes.set_pinned, team.interview.id, first.id, True),
            transaction(interview_notes.set_pinned, team.interview.id, second.id, True),
        )

        return both, await pinned(team.interview.id)

    assert run(scenario()) == ((None, None), ["Second"])


def test_the_database_refuses_a_second_pinned_note(run):
    async def scenario():
        team = await factories.team("unique")
        first = await note(team, "owner", "First")
        second = await note(team, "owner", "Second")
        await transaction(interview_notes.set_pinned, team.interview.id, first.id, True)

        with pytest.raises(IntegrityError):
            async with Session.begin() as session:
                await session.execute(
                    update(InterviewNote).where(InterviewNote.id == second.id).values(pinned=True)
                )

        return await pinned(team.interview.id)

    assert run(scenario()) == ["First"]


def test_each_interview_lists_its_note_count_and_pinned_note(run):
    async def scenario():
        team = await factories.team("summaries")
        quiet = await transaction(interviews.create, team.company.id, uuid.uuid4(), "en", 60)
        unpinned = await transaction(interviews.create, team.company.id, uuid.uuid4(), "en", 60)
        first = await note(team, "owner", "Hire")
        await note(team, "viewer", "Agreed")
        await transaction(interview_notes.set_pinned, team.interview.id, first.id, True)
        _, _, member = await factories.as_member(team.owner, team.interview.id)
        await transaction(interview_notes.add, unpinned, member.id, None, "Maybe")
        listed = await interviews_page(team.company.id, 0, 10)

        return {item.id: (item.note_count, item.pinned_note) for item in listed}, {
            "team": team.interview.id,
            "quiet": quiet.id,
            "unpinned": unpinned.id,
        }

    found, ids = run(scenario())

    assert found == {
        ids["team"]: (2, "Hire"),
        ids["quiet"]: (0, None),
        ids["unpinned"]: (1, None),
    }


def test_notes_go_with_their_interview_and_their_company(run):
    async def scenario():
        team = await factories.team("deleted")
        kept = await transaction(interviews.create, team.company.id, uuid.uuid4(), "en", 60)
        _, _, member = await factories.as_member(team.owner, team.interview.id)
        await note(team, "owner", "Goes with the interview")
        await transaction(interview_notes.add, kept, member.id, None, "Goes with the company")
        await factories.interview_removed(team.interview.id)
        after_interview = (
            await note_count(interview_id=team.interview.id),
            await note_count(company_id=team.company.id),
        )
        await factories.deleted(team.company.id)

        return after_interview, await note_count(company_id=team.company.id)

    assert run(scenario()) == ((0, 1), 0)


def test_the_data_download_has_the_notes_its_user_wrote(run):
    async def scenario():
        team = await factories.team("export")
        await note(team, "admin", "Mine")
        await note(team, "owner", "The owner's")

        async with Session() as session:
            return team, await accounts.export(session, team.admin, f"{team.admin}@example.com")

    team, exported = run(scenario())

    assert [
        (item["company"], item["text"], item["edited_at"]) for item in exported["interview_notes"]
    ] == [(team.company.name, "Mine", None)]
    assert exported["interview_notes"][0]["written_at"] is not None
