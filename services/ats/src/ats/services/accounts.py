from uuid import UUID

from ats.core.db import Session
from ats.helpers.notifications import connection_broken
from ats.repositories import ats, ats_candidates, ats_links
from ats.services import ats as integrations
from ats.services import outbox as outbox_service


async def remove_user(user_id: str, email: str) -> None:
    """An account is deleted, in one transaction: an ATS's records of them as a candidate go;
    the ATS connections they made stay with their companies, without their id, and each company
    whose connection stops working is told it needs reconnecting."""
    async with Session.begin() as session:
        await ats_candidates.delete_email(session, email)

        for company_id, provider in await ats.forget_maker(session, user_id):
            ats.notify(session, connection_broken(company_id, provider))

    await outbox_service.flush_quietly()


async def export_user(user_id: str, email: str) -> dict:
    """For "Download my data": what ATSs sent about them as a candidate, and the ATS connections
    they made."""
    async with Session() as session:
        candidates = await ats_candidates.of_email(session, email)
        connections = await ats.made_by(session, user_id)

    return {
        "ats_candidates": [
            {
                "email": row.email,
                "name": row.name,
                "interview_id": row.interview_id,
                "status": row.status,
                "results_sent_at": row.reported_at,
                "at": row.created_at,
            }
            for row in candidates
        ],
        "ats_connections": [
            {
                "company_id": row.company_id,
                "provider": row.provider,
                "account": row.account,
                "at": row.created_at,
            }
            for row in connections
        ],
    }


async def remove_candidate(interview_id: UUID, email: str) -> None:
    """A company erased a candidate: the ATS's record of them for that interview goes."""
    async with Session.begin() as session:
        await ats_candidates.delete_candidate(session, interview_id, email)


async def remove_interview(interview_id: UUID) -> None:
    """Workable's notifications for the interview's linked jobs are cancelled (as far as Workable
    answers), then its candidates go, a batch at a time, and then its links."""
    async with Session() as session:
        links = await ats_links.interview_links(session, interview_id)

    for link, connection in links:
        if link.subscription_id:
            await integrations.unsubscribe(connection, [link.subscription_id])

    await ats_candidates.delete_interview_candidates(Session, interview_id)

    async with Session.begin() as session:
        await ats_links.delete_interview_links(session, interview_id)


async def remove_company(company_id: UUID) -> None:
    """What prepza set up in the company's ATSs is cancelled (as far as each answers), then its
    connections go, with their linked jobs and candidates."""
    async with Session() as session:
        subscriptions = await ats_links.subscriptions(session, company_id)
        connections = await ats.connections(session, company_id)

    for connection in connections:
        await integrations.release(connection, subscriptions)

    async with Session.begin() as session:
        await ats.delete_company(session, company_id)
