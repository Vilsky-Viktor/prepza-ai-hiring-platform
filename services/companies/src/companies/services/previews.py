from uuid import uuid4

from fastapi import HTTPException, status
from prepza_common.ai.multi_answer import multi_share
from prepza_common.events.analytics import track
from prepza_common.limits.rate_limit import hit_or_skip

from companies.helpers.interviews import session_topics
from companies.integrations import library, rounds
from companies.integrations.redis import get_redis
from companies.models.interviews import Interview
from companies.services.interview_views import attach_set


async def preview(interview: Interview, user_id: str) -> str:
    """A company member takes their own test as a candidate would: free, kept out of the
    candidate list, and its answers out of the questions' statistics. Returns its first
    session's id."""
    interview = await attach_set(interview)
    content = await library.get_content(interview.set_id) if interview.set_id else None

    if content is None or not content["topics"]:
        raise HTTPException(status.HTTP_409_CONFLICT, "Interview is not ready yet")

    # Counted once it would start (a test not ready yet isn't a preview), against floods: with
    # Redis down, not counted rather than refused.
    await hit_or_skip(
        get_redis(),
        f"rate:previews:{user_id}",
        "PREVIEWS_PER_USER_HOUR",
        company_id=interview.company_id,
        user_id=user_id,
    )

    # No invite stands behind a preview, so finishing it charges nothing.
    created = await rounds.create_sessions(
        {
            "user_id": user_id,
            "company_id": str(interview.company_id),
            "candidate_invite_id": str(uuid4()),
            "question_seconds": interview.question_seconds,
            "topics": session_topics(interview, content, await multi_share(get_redis())),
            "preview": True,
        }
    )
    await track("interview_previewed", user_id=user_id, company_id=interview.company_id)

    return created[0]["id"]
