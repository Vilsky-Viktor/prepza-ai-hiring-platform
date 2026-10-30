from fastapi import HTTPException, status
from prepza_common.ai.multi_answer import multi_share
from prepza_common.auth.user import User
from prepza_common.i18n.names import clean_name
from prepza_common.limits.pause import refuse_if_paused

from companies.constants.invites import EMAIL_NOT_VERIFIED, NOT_THE_GUEST, InviteStatus
from companies.core.db import Session
from companies.helpers.candidates import candidate_seconds
from companies.helpers.interviews import session_topics
from companies.integrations import library, rounds
from companies.integrations.firebase_tokens import guest_uid
from companies.integrations.redis import get_redis
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import companies, invite_progress
from companies.schemas.invites import InviteStartOut, SessionSummary
from companies.services.access import open_invite, refuse_if_suspended, refuse_without_pledge
from companies.services.candidate_billing import hold_again
from companies.services.interview_views import attach_set


async def start_sessions(
    invite: CandidateInvite, interview: Interview, user: User
) -> InviteStartOut:
    """Starts (or returns) the candidate's sessions: one per topic, with fresh random questions,
    and marks the invite in process. The candidate's name comes only from their verified sign-in
    (`user`), never from the request, and fills only a name not known yet."""
    interview = await attach_set(interview)

    if interview.set_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Interview is not ready yet")

    content = await library.get_content(interview.set_id)

    if content is None or not content["topics"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Interview content not found")

    # Sessions first: if rounds fails, the invite stays unstarted, so expiry gives its credits
    # back. Starting again returns the sessions already made.
    created = await rounds.create_sessions(
        {
            "user_id": user.uid,
            "company_id": str(interview.company_id),
            "candidate_invite_id": str(invite.id),
            "question_seconds": candidate_seconds(interview.question_seconds, invite.extra_time),
            "topics": session_topics(interview, content, await multi_share(get_redis())),
            "voice": bool(interview.voice),
        }
    )

    async with Session.begin() as session:
        before = await invite_progress.start(session, invite.id, user.uid, clean_name(user.name))

    # Revoked meanwhile: its sessions go too.
    if before is None:
        await rounds.delete_invite_sessions([invite.id])

        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invite not found")

    # Expired after it was read: expiry gave its credits back.
    if before == InviteStatus.EXPIRED:
        await hold_again(invite, invite.hold_key)

    return InviteStartOut(
        sessions=[
            SessionSummary(id=row["id"], topic_title=row["topic_title"], status=row["status"])
            for row in created
        ]
    )


async def start_invite(token: str, user: User, pledged: bool) -> InviteStartOut:
    """Only the invited, verified email can start, so a forwarded link is useless to anyone else;
    a guest invite, only its guest (its link signs them in). A first start takes the candidate's
    pledge to answer on their own; while paused, only a candidate already in the interview goes
    on."""
    invite, interview = await open_invite(token)

    if invite.guest:
        if user.uid != guest_uid(invite.id):
            raise HTTPException(status.HTTP_403_FORBIDDEN, NOT_THE_GUEST)
    elif not user.email_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, EMAIL_NOT_VERIFIED)
    elif user.email.lower() != invite.email:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "This invite was sent to a different email address"
        )

    if invite.status == InviteStatus.FINISHED:
        raise HTTPException(status.HTTP_409_CONFLICT, "This interview is already finished")

    async with Session() as session:
        company = await companies.get(session, interview.company_id)

    refuse_if_suspended(company, invite.status)
    refuse_without_pledge(pledged, invite.status)

    # Paused, nobody starts; a candidate already in the interview may finish it.
    if invite.status != InviteStatus.IN_PROCESS:
        await refuse_if_paused(get_redis(), "interview_start", interview.company_id, user.uid)

    return await start_sessions(invite, interview, user)
