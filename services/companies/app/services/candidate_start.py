from fastapi import HTTPException, status
from prepza_common.ai.multi_answer import multi_share
from prepza_common.auth.user import User
from prepza_common.i18n.names import clean_name

from app.constants.invites import InviteStatus
from app.helpers.candidates import candidate_seconds
from app.helpers.interviews import attach_set, session_topics
from app.integrations import library, rounds
from app.integrations.redis import get_redis
from app.models.interviews import Interview
from app.models.invites import CandidateInvite
from app.schemas.invites import InviteStartOut, SessionSummary
from app.services.candidate_billing import hold_again
from app.storage import invite_progress


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
        }
    )

    before = await invite_progress.start(invite.id, user.uid, clean_name(user.name))

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
