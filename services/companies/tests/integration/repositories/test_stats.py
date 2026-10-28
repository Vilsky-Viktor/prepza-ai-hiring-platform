import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import update

from companies.constants.verification import VerificationStatus
from companies.core.db import Session
from companies.models.companies import Company
from companies.repositories import interviews, invite_progress, link_invites, stats
from tests.integration import factories
from tests.integration.transactions import transaction


async def set_company(company_id, **values):
    async with Session() as session:
        await session.execute(update(Company).where(Company.id == company_id).values(**values))
        await session.commit()


def test_counts_only_what_the_month_added(run):
    now = datetime.now(UTC)
    month = now.strftime("%Y-%m")

    async def scenario():
        before, before_all = (
            await transaction(stats.stats, month),
            await transaction(stats.stats, None),
        )
        before_year = await transaction(stats.stats, now.strftime("%Y"))
        company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        found = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
        finished = await transaction(link_invites.for_link, found.id, "done@example.com")
        await transaction(invite_progress.finish, finished.id, 80, False, None)
        await transaction(link_invites.for_link, found.id, "waiting@example.com")
        await set_company(
            company.id,
            verification_status=VerificationStatus.APPROVED,
            verification_decided_at=now,
        )
        # Created last month: not this month's.
        older = await factories.company(f"Older {uuid.uuid4()}", "owner", "owner@example.com")
        await set_company(older.id, created_at=now.replace(day=1) - timedelta(days=1))
        after, after_all = (
            await transaction(stats.stats, month),
            await transaction(stats.stats, None),
        )
        after_year = await transaction(stats.stats, now.strftime("%Y"))

        return (
            {name: after[name] - before[name] for name in after},
            after_all["companies"] - before_all["companies"],
            after_year["companies"] - before_year["companies"],
        )

    this_month, all_time, this_year = run(scenario())

    # All time has last month's company too, and so has this year unless it's January.
    assert all_time == 2
    assert this_year == (1 if now.month == 1 else 2)
    assert this_month == {
        "companies": 1,
        "verified": 1,
        "interviews": 1,
        "invited": 2,
        "finished": 1,
    }
