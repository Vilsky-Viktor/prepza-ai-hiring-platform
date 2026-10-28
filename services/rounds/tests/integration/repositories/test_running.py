import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import update

from rounds.constants.rounds import RoundStatus
from rounds.core.db import Session as Db
from rounds.models.sessions import Session
from rounds.repositories import running, session_expiry, sessions
from tests.integration.factories import created, topic
from tests.integration.transactions import transaction


async def shown(row, ago):
    async with Db() as db:
        await db.execute(
            update(Session)
            .where(Session.id == row.id)
            .values(question_shown_at=datetime.now(UTC) - ago)
        )
        await db.commit()


def test_running_counts_candidates_with_a_question_on_screen_now(run):
    async def scenario():
        before = await transaction(running.running_interviews)
        invite = uuid.uuid4()
        both = await created("ann", invite, [topic(), topic()], 30, company_id=uuid.uuid4())
        [idle] = await created("bob", uuid.uuid4(), [topic()], 30, company_id=uuid.uuid4())
        [preview] = await created(
            "cto", uuid.uuid4(), [topic()], 30, preview=True, company_id=uuid.uuid4()
        )
        await created("dan", uuid.uuid4(), [topic()], 30, company_id=uuid.uuid4())

        for row in both:
            await shown(row, timedelta(minutes=1))

        await shown(idle, timedelta(hours=1))
        await shown(preview, timedelta(minutes=1))

        return await transaction(running.running_interviews) - before

    # Ann's interview once for its two sections; Bob left an hour ago, the preview doesn't
    # count and Dan has no question on screen.
    assert run(scenario()) == 1


def test_running_interviews_get_back_the_time_maintenance_mode_was_on(run):
    async def scenario():
        # Ann's 6-minute interview (2 sections, 3 questions at 60 seconds) started 7 minutes ago,
        # past its time with the margin; her first section is done and a question is on screen.
        ann = uuid.uuid4()
        first, second = await created("ann", ann, [topic(), topic()], 60, company_id=uuid.uuid4())
        # Bob finished; his interview isn't running.
        [done] = await created("bob", uuid.uuid4(), [topic()], 60, company_id=uuid.uuid4())

        async with Db() as db:
            await db.execute(
                update(Session)
                .where(Session.id.in_([first.id, second.id, done.id]))
                .values(started_at=datetime.now(UTC) - timedelta(minutes=7))
            )
            await db.execute(
                update(Session)
                .where(Session.id.in_([first.id, done.id]))
                .values(status=RoundStatus.FINISHED)
            )
            await db.commit()

        await shown(second, timedelta(seconds=50))
        before = {row.id: await transaction(sessions.get, row.id) for row in (first, second, done)}
        expired = await transaction(session_expiry.expired_invites, datetime.now(UTC), 1, ann)

        await transaction(running.give_time_back, timedelta(minutes=10))

        after = {row.id: await transaction(sessions.get, row.id) for row in (first, second, done)}
        still = await transaction(session_expiry.expired_invites, datetime.now(UTC), 1, ann)

        return before, after, expired, still, (first.id, second.id, done.id)

    before, after, expired, still, (first, second, done) = run(scenario())
    ten = timedelta(minutes=10)

    assert expired and not still
    assert after[first].started_at - before[first].started_at == ten
    assert after[second].started_at - before[second].started_at == ten
    assert after[second].question_shown_at - before[second].question_shown_at == ten
    assert after[done].started_at == before[done].started_at
