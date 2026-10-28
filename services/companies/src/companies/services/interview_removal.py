"""An interview going: deleted by an owner or admin once it has its questions, or with its
generation cancelled before."""

from fastapi import HTTPException, status
from prepza_common.events.audit_actions import AuditAction
from prepza_common.http.http import passed_on

from companies.constants.generation import GENERATION_REFUSALS
from companies.core.db import Session
from companies.integrations import generation as generation_api
from companies.integrations import library, rounds
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import audit, interviews
from companies.services import batch_deletion
from companies.services.candidate_billing import release_unfinished, settle_unfinished
from companies.services.interview_views import attach_set


async def remove(interview: Interview, user_id: str | None = None) -> list[tuple]:
    """Deletes the interview, its invites first a batch at a time (cut off midway, it goes on
    when run again), then the interview with the interview.deleted event and, with `user_id`,
    its line in the action log, in one save. Returns (interview id, email, status, hold key) of
    its invites not finished, deleted with it."""
    removed = await batch_deletion.delete_invites(CandidateInvite.interview_id == interview.id)

    async with Session.begin() as session:
        removed += await interviews.remove(session, interview.id)

        if user_id is not None:
            await audit.record_interview(session, interview, user_id, AuditAction.INTERVIEW_DELETED)

    return removed


async def delete(interview: Interview, user_id: str) -> None:
    """Credits, results and questions go first, so a failure leaves the interview to delete
    again; one still generating is cancelled instead (409)."""
    interview = await attach_set(interview)

    if interview.set_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cancel the generation instead")

    # Settled while rounds still has the answers. Released again as it's removed, for an invite
    # made or sent again meanwhile; a charged candidate stays charged.
    await settle_unfinished(interview.id)
    await rounds.delete_interview_data(interview.set_id)
    await library.delete_interview(interview.set_id)
    await release_unfinished(await remove(interview, user_id))


async def cancel_generation(interview: Interview) -> dict:
    """Removes the interview too, so it isn't left without questions; generation's answer."""
    cancelled = passed_on(
        await generation_api.cancel(interview.generation_id, interview.company_id),
        GENERATION_REFUSALS,
    ).json()
    await remove(interview)

    return cancelled
