from companies.constants.reports import READ_BATCH
from companies.core.db import Session
from companies.helpers.candidates import candidate_out
from companies.helpers.logos import logo_path
from companies.integrations import rounds
from companies.models.companies import Company
from companies.models.interviews import Interview
from companies.repositories import candidates
from companies.schemas.reports import InterviewReportOut
from companies.services import candidate_results
from companies.services.interview_views import interview_title


async def batch(interview: Interview, offset: int) -> list:
    async with Session() as session:
        return await candidates.for_report(session, interview.id, offset, READ_BATCH)


async def report(interview: Interview, company: Company) -> InterviewReportOut:
    """Every candidate but deleted ones, best grade first, with their results: a batch at a
    time, with its candidates' scores, until one comes up short."""
    await candidate_results.backfill(interview.id)
    every, totals = [], {}

    while True:
        rows = await batch(interview, len(every))
        every += rows
        totals |= await rounds.invite_scores([invite.id for invite in rows])

        if len(rows) < READ_BATCH:
            break

    return InterviewReportOut(
        title=await interview_title(interview),
        company=company.name,
        logo_url=logo_path(company),
        verified_domain=company.verified_domain,
        pass_mark=interview.pass_mark,
        candidates=[
            candidate_out(invite, totals.get(str(invite.id)) or {}, interview) for invite in every
        ],
    )
