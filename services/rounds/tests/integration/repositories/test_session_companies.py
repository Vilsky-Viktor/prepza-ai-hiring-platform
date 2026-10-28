"""Companies' backfill gives old interview sections their company; practice needs none."""

import uuid

import pytest
from sqlalchemy import select, text, update
from sqlalchemy.exc import IntegrityError

from rounds.core.db import Session as Db
from rounds.models.sessions import Session
from rounds.repositories import session_companies
from tests.integration.factories import created, topic
from tests.integration.transactions import transaction

CHECK = "ck_sessions_company_id"


def test_old_sections_get_their_sets_company_once(run):
    company = uuid.uuid4()

    async def scenario():
        section = topic()
        [row] = await created("ann", uuid.uuid4(), [section], 60, company_id=company)

        # As a section started before rounds kept its company: the check is lifted for the
        # moment, then made and validated again, as the migration does.
        async with Db() as session:
            await session.execute(text(f"ALTER TABLE sessions DROP CONSTRAINT {CHECK}"))
            await session.execute(
                update(Session).where(Session.id == row.id).values(company_id=None)
            )
            await session.commit()

        try:
            filled = await transaction(session_companies.fill, {section.preparation_id: company})
            again = await transaction(session_companies.fill, {section.preparation_id: company})
        finally:
            async with Db() as session:
                await session.execute(
                    text(
                        f"ALTER TABLE sessions ADD CONSTRAINT {CHECK} "
                        "CHECK (practice OR company_id IS NOT NULL)"
                    )
                )
                await session.commit()

        async with Db() as session:
            kept = await session.scalar(select(Session.company_id).where(Session.id == row.id))

        return filled, again, kept

    assert run(scenario()) == (1, 0, company)


def test_an_interview_section_needs_its_company_and_practice_none(run):
    async def scenario():
        await created("ann", uuid.uuid4(), [topic()], 60, practice=True)

        with pytest.raises(IntegrityError) as refused:
            await created("ann", uuid.uuid4(), [topic()], 60)

        return refused.value.orig.diag.constraint_name

    assert run(scenario()) == CHECK
