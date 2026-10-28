"""companies' interview.deleted and company.deleted take the sessions of what went (rule 11:
a redelivery deletes nothing more, and the events work in any order)."""

import uuid

from sqlalchemy import func, select

from rounds.core.db import Session as Db
from rounds.handlers.dispatch import handle
from rounds.models.sessions import Session
from tests.integration.factories import created, topic


def on(interview_set_id: uuid.UUID):
    """A topic of that interview."""
    return topic().model_copy(update={"preparation_id": interview_set_id})


async def count(*conditions) -> int:
    async with Db() as session:
        return await session.scalar(select(func.count()).select_from(Session).where(*conditions))


def interview_deleted(company_id, set_id) -> dict:
    return {
        "interview_id": str(uuid.uuid4()),
        "company_id": str(company_id),
        "set_id": str(set_id) if set_id else None,
        "generation_id": str(uuid.uuid4()),
    }


def test_a_deleted_interviews_sessions_go_once_and_others_stay(run):
    company_id, deleted, kept = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

    async def scenario():
        await created("cand-a", uuid.uuid4(), [on(deleted)], 30, company_id=company_id)
        await created("bob", uuid.uuid4(), [on(deleted)], 30, preview=True, company_id=company_id)
        await created("cand-b", uuid.uuid4(), [on(kept)], 30, company_id=company_id)
        event = interview_deleted(company_id, deleted)
        await handle("interview.deleted", event)
        # Redelivered: nothing more goes.
        await handle("interview.deleted", event)

        return (
            await count(Session.interview_set_id == deleted),
            await count(Session.interview_set_id == kept),
        )

    assert run(scenario()) == (0, 1)


def test_an_interview_deleted_while_generating_names_no_sessions(run):
    company_id = uuid.uuid4()

    async def scenario():
        await created("cand-a", uuid.uuid4(), [on(uuid.uuid4())], 30, company_id=company_id)
        await handle("interview.deleted", interview_deleted(company_id, None))

        return await count(Session.company_id == company_id)

    assert run(scenario()) == 1


def test_a_deleted_companys_sessions_go_whatever_came_first(run):
    """company.deleted before or after its interviews' events, and again: every session of the
    company goes, another company's stay."""
    company_id, other, set_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

    async def scenario():
        await created("cand-a", uuid.uuid4(), [on(set_id)], 30, company_id=company_id)
        await created("cand-b", uuid.uuid4(), [on(uuid.uuid4())], 30, company_id=company_id)
        await created("cand-c", uuid.uuid4(), [on(uuid.uuid4())], 30, company_id=other)
        await handle("company.deleted", {"company_id": str(company_id)})
        await handle("interview.deleted", interview_deleted(company_id, set_id))
        await handle("company.deleted", {"company_id": str(company_id)})

        return await count(Session.company_id == company_id), await count(
            Session.company_id == other
        )

    assert run(scenario()) == (0, 1)
