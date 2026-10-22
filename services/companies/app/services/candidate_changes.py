from fastapi import HTTPException, status
from prepza_common.audit_actions import AuditAction, TargetKind

from app.constants.invites import CHANGE_ACTIONS, EXTRA_TIME_STARTED, NOT_STARTED, InviteStatus
from app.integrations import rounds
from app.models.interviews import Interview
from app.models.invites import CandidateInvite
from app.services import outbox as outbox_service
from app.services.candidate_billing import settle_removed
from app.storage import audit, invites


async def remove(
    interview: Interview, invite: CandidateInvite, user_id: str, via: str | None
) -> None:
    """Withdraws an invite the candidate hasn't used yet. Once they've started, it erases them for
    good, answers and results included, for example when they ask to have their data deleted.
    A candidate who answered at least one question is charged; other credits still held come
    back. `user_id`, an owner or admin, is recorded with `via` (assistant, mcp or api)."""
    if invite.status != InviteStatus.FINISHED:
        await settle_removed([invite])

    if invite.status not in NOT_STARTED:
        await rounds.delete_invite_sessions([invite.id])

    removed = await invites.remove(invite, interview.company_id)

    # Started since it was read: the sessions it made go too.
    if invite.status in NOT_STARTED and removed == InviteStatus.IN_PROCESS:
        await rounds.delete_invite_sessions([invite.id])

    await outbox_service.flush_quietly()
    revoked = invite.status in NOT_STARTED
    action = AuditAction.INVITE_REVOKED if revoked else AuditAction.CANDIDATE_DELETED
    await audit.record(
        interview.company_id, user_id, action, invite.id, via=via, target_kind=TargetKind.CANDIDATE
    )


async def change(
    interview: Interview,
    invite: CandidateInvite,
    values: dict,
    user_id: str,
    via: str | None = None,
) -> None:
    """Corrects the candidate's name (`name`; none makes it not known, and the sign-in fills only
    a name not known, so this one stays) and gives them extra time on each question
    (`extra_time`, until they start), all or nothing: every rule is checked before anything is
    written, and both are written at once. A deleted candidate is 404; extra time for one who
    started, 409. Each change is recorded for `user_id`, with `via`."""
    timed = "extra_time" in values

    if invite.status == InviteStatus.DELETED:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidate not found")

    if timed and invite.status not in NOT_STARTED:
        raise HTTPException(status.HTTP_409_CONFLICT, EXTRA_TIME_STARTED)

    statuses = (
        NOT_STARTED if timed else [item for item in InviteStatus if item != InviteStatus.DELETED]
    )

    # Started, or deleted, since it was read.
    if values and not await invites.change(invite.id, values, statuses):
        if timed:
            raise HTTPException(status.HTTP_409_CONFLICT, EXTRA_TIME_STARTED)

        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidate not found")

    for field, action in CHANGE_ACTIONS.items():
        if field in values:
            await audit.record(
                interview.company_id,
                user_id,
                action,
                invite.id,
                via=via,
                target_kind=TargetKind.CANDIDATE,
            )
