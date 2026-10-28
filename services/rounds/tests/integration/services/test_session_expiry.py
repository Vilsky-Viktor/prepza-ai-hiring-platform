import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from rounds.constants.events import INTERVIEW_FINISHED
from rounds.constants.rounds import RoundStatus
from rounds.core.db import Session as Db
from rounds.models.answers import Answer
from rounds.models.outbox import OutboxEvent
from rounds.models.sessions import Session
from rounds.repositories import sessions
from rounds.services import sections, session_expiry
from tests.integration.factories import created, option_index, topic
from tests.integration.transactions import transaction


async def interview(started_minutes_ago: float):
    """A candidate's interview of two sections, 3 questions each at 60 seconds: 6 minutes in
    all, 6.6 with the margin."""
    invite_id = uuid.uuid4()
    rows = await created("cand", invite_id, [topic(), topic()], 60, company_id=uuid.uuid4())

    async with Db() as db:
        await db.execute(
            update(Session)
            .where(Session.candidate_invite_id == invite_id)
            .values(started_at=datetime.now(UTC) - timedelta(minutes=started_minutes_ago))
        )
        await db.commit()

    return invite_id, rows


def test_an_interview_left_past_its_time_finishes_by_itself(run):
    async def scenario():
        _, expired_rows = await interview(started_minutes_ago=7)
        _, running_rows = await interview(started_minutes_ago=6)

        await session_expiry.finish_expired()

        return (
            [await transaction(sessions.get, row.id) for row in expired_rows],
            [await transaction(sessions.get, row.id) for row in running_rows],
        )

    expired, running = run(scenario())

    assert [row.status for row in expired] == [RoundStatus.FINISHED] * 2
    # Nothing was answered, so every question counts as wrong.
    assert [row.final_score for row in expired] == [0, 0]
    # Still within its time plus the 10% margin.
    assert [row.status for row in running] == [RoundStatus.IN_PROGRESS] * 2


def test_a_candidate_coming_back_late_finds_the_interview_finished(run):
    async def scenario():
        late_id, late_rows = await interview(started_minutes_ago=30)
        on_time_id, _ = await interview(started_minutes_ago=1)

        return (
            await session_expiry.finish_if_expired(late_id),
            await session_expiry.finish_if_expired(on_time_id),
            await transaction(sessions.get, late_rows[0].id),
        )

    late, on_time, row = run(scenario())

    assert (late, on_time) == (True, False)
    assert row.status == RoundStatus.FINISHED


def test_the_last_section_finishing_announces_the_interview_with_its_answers(run):
    async def scenario():
        invite_id, rows = await interview(started_minutes_ago=1)
        question = rows[0].questions[0]
        await transaction(
            sessions.add_answer,
            Answer(
                session_id=rows[0].id,
                question_id=uuid.UUID(question["id"]),
                option_index=option_index(question, True),
                correct=True,
                score=100,
            ),
        )
        await transaction(sections.finish, rows[0].id)
        after_first = await announced(invite_id)
        await transaction(sections.finish, rows[1].id)
        await transaction(sections.finish, rows[1].id)

        return after_first, await announced(invite_id)

    after_first, after_last = run(scenario())

    assert after_first == []
    # Announced once, with the one answer the candidate picked.
    assert after_last == [
        {"candidate_invite_id": after_last[0]["candidate_invite_id"], "answered": 1}
    ]


async def announced(invite_id):
    async with Db() as db:
        rows = await db.scalars(
            select(OutboxEvent.data).where(OutboxEvent.event_type == INTERVIEW_FINISHED)
        )

        return [data for data in rows if data["candidate_invite_id"] == str(invite_id)]
