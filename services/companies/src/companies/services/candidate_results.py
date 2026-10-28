"""Candidates' results from rounds, stored on their invites once they finish, so the candidates
list sorts and filters by them in SQL."""

from datetime import datetime
from uuid import UUID

from companies.constants.invites import RESULT_FILTERS, InviteStatus
from companies.helpers.candidates import candidate_out, company_candidate_out, stored_results
from companies.integrations import rounds
from companies.repositories import candidates


async def sync(listed: list, totals: dict[str, dict]) -> None:
    """Stores the results of listed candidates rounds says finished whose invite doesn't have
    them yet (interview.finished is still on its way, or rounds didn't answer when it came), and
    shows them finished; the status itself is stored by that event (candidates.save_results)."""
    results = {
        invite.id: stored_results(totals[str(invite.id)])
        for invite in listed
        if (totals.get(str(invite.id)) or {}).get("finished")
        and (
            invite.status != InviteStatus.FINISHED
            or (invite.grade, invite.flagged) != stored_results(totals[str(invite.id)])
        )
    }
    await candidates.save_results(results)

    for invite in listed:
        if invite.id in results:
            invite.status = InviteStatus.FINISHED
            invite.grade, invite.flagged = results[invite.id]


async def backfill(interview_id) -> None:
    """Stores the results of the interview's finished candidates that don't have them: finished
    before results were stored, or rounds didn't answer then. Usually there are none."""
    missing = await candidates.unscored(interview_id)

    if not missing:
        return

    totals = await rounds.invite_scores(missing)
    await candidates.save_results(
        {
            invite_id: stored_results(totals[str(invite_id)])
            for invite_id in missing
            if str(invite_id) in totals
        }
    )


async def page(
    interview,
    offset: int,
    limit: int,
    by_grade: bool,
    q: str = "",
    filter_by: str | None = None,
    with_link: bool = False,
    since: datetime | None = None,
    after: UUID | None = None,
) -> list:
    """A page of the interview's candidates with their results: best grade first or newest
    first, narrowed to an email containing `q` and a status or result, all in SQL on the results
    stored when candidates finish. Progress and signals come from rounds for this page only."""
    if by_grade or filter_by in RESULT_FILTERS:
        await backfill(interview.id)

    listed = await candidates.page(
        interview.id, offset, limit, by_grade, q, filter_by, interview.pass_mark, since, after
    )
    totals = await rounds.invite_scores([invite.id for invite in listed])
    await sync(listed, totals)

    return [
        candidate_out(invite, totals.get(str(invite.id)) or {}, interview, with_link)
        for invite in listed
    ]


async def company_page(
    company_id, offset: int, limit: int, q: str = "", email: str = "", with_link: bool = False
) -> list:
    """A page of the company's candidates across its interviews, newest first, narrowed to an
    email containing `q`, or to exactly `email`; progress and signals come from rounds for this
    page only, as in page. `with_link` adds the invite link's token (the public API)."""
    listed = await candidates.company_page(company_id, offset, limit, q, email)
    found = [invite for invite, _ in listed]
    totals = await rounds.invite_scores([invite.id for invite in found])
    await sync(found, totals)

    return [
        company_candidate_out(invite, totals.get(str(invite.id)) or {}, interview, with_link)
        for invite, interview in listed
    ]
