import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import update

from rounds.core.db import Session
from rounds.models.sessions import Session as RoundSession
from rounds.repositories import stats
from tests.integration.factories import created, topic
from tests.integration.transactions import transaction


def test_a_practice_round_counts_once_in_the_month_it_started(run):
    now = datetime.now(UTC)
    month = now.strftime("%Y-%m")

    async def scenario():
        before = (await transaction(stats.stats, month))["practice"]
        # A practice round of two sections, and a company candidate's interview.
        await created("talent", uuid.uuid4(), [topic(), topic()], 30, practice=True)
        await created("candidate", uuid.uuid4(), [topic()], 30, company_id=uuid.uuid4())
        # A practice round started last month.
        older = uuid.uuid4()
        await created("talent", older, [topic()], 30, practice=True)

        async with Session() as session:
            await session.execute(
                update(RoundSession)
                .where(RoundSession.candidate_invite_id == older)
                .values(started_at=now.replace(day=1) - timedelta(days=1))
            )
            await session.commit()

        return (await transaction(stats.stats, month))["practice"] - before

    assert run(scenario()) == 1
