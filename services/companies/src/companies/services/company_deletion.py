from prepza_common.db.db import delete_in_batches

from companies.constants.reports import READ_BATCH
from companies.core.db import Session
from companies.integrations import billing
from companies.integrations import generation as generation_api
from companies.models.interview_notes import InterviewNote
from companies.models.invites import CandidateInvite
from companies.repositories import audit, companies, interviews
from companies.services import batch_deletion, outbox
from companies.services.interview_views import attach_set


async def interviews_after(company_id, after) -> list:
    async with Session() as session:
        return await interviews.page_by_id(session, company_id, after, READ_BATCH)


async def delete_company(company_id) -> None:
    """Each interview's generation stops first, then its credits and automatic top-up go, so a
    failure leaves the company to delete again; then its rows (delete_rows), whose events tell
    rounds and library to delete the results and questions."""
    after = None

    while page := await interviews_after(company_id, after):
        after = page[-1].id

        for interview in page:
            await stop_generation(company_id, interview)

    await billing.delete_company(company_id)
    await delete_rows(company_id)


async def delete_rows(company_id) -> None:
    """The company's own rows: its invites, action log, notes and interviews (each with
    interview.deleted) a batch at a time, then the company with its members and the
    company.deleted event."""
    await batch_deletion.delete_invites(CandidateInvite.company_id == company_id)
    await audit.delete_company(Session, company_id)
    await delete_in_batches(Session, InterviewNote, InterviewNote.company_id == company_id)
    await batch_deletion.delete_interviews(company_id)

    async with Session.begin() as session:
        await companies.delete(session, company_id)

    await outbox.flush_quietly()


async def stop_generation(company_id, interview) -> None:
    """An interview still generating is cancelled, and its set saved meanwhile noted, so its
    interview.deleted names the questions library deletes."""
    if interview.set_id is not None:
        return

    cancelled = await generation_api.cancel(interview.generation_id, company_id)

    if cancelled.is_server_error:
        cancelled.raise_for_status()

    await attach_set(interview)
