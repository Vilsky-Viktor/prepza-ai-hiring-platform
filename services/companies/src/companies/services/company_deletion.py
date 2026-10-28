from companies.constants.reports import READ_BATCH
from companies.core.db import Session
from companies.integrations import billing, library, rounds
from companies.integrations import generation as generation_api
from companies.models.invites import CandidateInvite
from companies.repositories import audit, companies, interviews
from companies.services import batch_deletion, outbox
from companies.services.interview_views import attach_set


async def interviews_after(company_id, after) -> list:
    async with Session() as session:
        return await interviews.page_by_id(session, company_id, after, READ_BATCH)


async def delete_company(company_id) -> None:
    """Each interview's results and questions go first, then its credits and automatic top-up,
    so a failure leaves the company to delete again; then its rows (delete_rows)."""
    after = None

    while page := await interviews_after(company_id, after):
        after = page[-1].id

        for interview in page:
            await delete_interview_data(company_id, interview)

    await billing.delete_company(company_id)
    await delete_rows(company_id)


async def delete_rows(company_id) -> None:
    """The company's own rows: its invites, action log and interviews a batch at a time, then
    the company with its members and the company.deleted event."""
    await batch_deletion.delete_invites(CandidateInvite.company_id == company_id)
    await audit.delete_company(Session, company_id)
    await batch_deletion.delete_interviews(company_id)

    async with Session.begin() as session:
        await companies.delete(session, company_id)

    await outbox.flush_quietly()


async def delete_interview_data(company_id, interview) -> None:
    """The interview's generation stops, and its results and questions go."""
    if interview.set_id is None:
        cancelled = await generation_api.cancel(interview.generation_id, company_id)

        if cancelled.is_server_error:
            cancelled.raise_for_status()

        interview = await attach_set(interview)

    if interview.set_id:
        await rounds.delete_interview_data(interview.set_id)
        await library.delete_interview(interview.set_id)
