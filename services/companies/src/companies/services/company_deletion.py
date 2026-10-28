from companies.constants.reports import READ_BATCH
from companies.helpers.interviews import attach_set
from companies.integrations import billing, library, rounds
from companies.integrations import generation as generation_api
from companies.repositories import companies, interviews
from companies.services import outbox


async def delete_company(company_id) -> None:
    """Each interview's results and questions go first, then its credits and automatic top-up,
    so a failure leaves the company to delete again. Its notifications go through the
    company.deleted event."""
    after = None

    while page := await interviews.page_by_id(company_id, after, READ_BATCH):
        after = page[-1].id

        for interview in page:
            await delete_interview_data(company_id, interview)

    await billing.delete_company(company_id)
    await companies.delete(company_id)
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
