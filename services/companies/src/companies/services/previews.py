import logging
from uuid import uuid4

from fastapi import HTTPException, status
from testee_common.ai.multi_answer import multi_share
from testee_common.events.analytics import track
from testee_common.limits.limit_list import LIMITS
from testee_common.limits.rate_limit import counted, hit, hit_or_skip

from companies.constants.interviews import PREVIEWS_USED_UP, VOICE_PREVIEWS_USED_UP
from companies.core.db import Session
from companies.helpers.interviews import session_topics
from companies.integrations import library, rounds
from companies.integrations.redis import get_redis
from companies.models.interviews import Interview
from companies.repositories import interviews
from companies.services.interview_views import attach_set

logger = logging.getLogger(__name__)


async def preview(interview: Interview, user_id: str) -> str:
    """A company member takes their own test as a candidate would: free, kept out of the
    candidate list, and its answers out of the questions' statistics. Returns its first
    session's id."""
    interview = await attach_set(interview)
    content = await library.get_content(interview.set_id) if interview.set_id else None

    if content is None or not content["topics"]:
        raise HTTPException(status.HTTP_409_CONFLICT, "Interview is not ready yet")

    # Counted once it would start (a test not ready yet isn't a preview): the person's hourly
    # limit first, then their company's daily one.
    redis = get_redis()
    who = {"company_id": interview.company_id, "user_id": user_id}
    await hit_or_skip(redis, f"rate:previews:{user_id}", "PREVIEWS_PER_USER_HOUR", **who)
    daily, key = await count_daily(redis, interview, who)

    try:
        created = await start(interview, content, user_id)
    except Exception:
        # Nothing started: the attempt gives back its place in the day's count.
        await give_back(redis, key, daily)
        raise

    await track("interview_previewed", **who)

    return created[0]["id"]


async def count_daily(redis, interview: Interview, who: dict) -> tuple[str, str]:
    """Counts one of the company's previews today: voice mode's apart, as it spends on reading
    aloud and hearing answers, so its limit fails closed (Redis down: refused); the others'
    only stops floods, so it fails open. Returns the limit's name and key."""
    if interview.voice:
        daily, key = "VOICE_PREVIEWS_PER_COMPANY_DAY", f"rate:previews:voice:{interview.company_id}"
        await hit(redis, key, daily, VOICE_PREVIEWS_USED_UP, **who)
    else:
        daily, key = "PREVIEWS_PER_COMPANY_DAY", f"rate:previews:company:{interview.company_id}"
        await hit_or_skip(redis, key, daily, PREVIEWS_USED_UP, **who)

    return daily, key


async def start(interview: Interview, content: dict, user_id: str) -> list[dict]:
    """The preview's sessions in rounds; gone again if the interview was deleted meanwhile."""
    # No invite stands behind a preview, so finishing it charges nothing.
    preview_id = uuid4()
    created = await rounds.create_sessions(
        {
            "user_id": user_id,
            "company_id": str(interview.company_id),
            "candidate_invite_id": str(preview_id),
            "question_seconds": interview.question_seconds,
            "topics": session_topics(interview, content, await multi_share(get_redis())),
            "preview": True,
            "voice": bool(interview.voice),
        }
    )
    await gone_meanwhile(interview.id, preview_id)

    return created


async def give_back(redis, key: str, name: str) -> None:
    """Takes back one count of a preview that didn't start; with Redis down, it stays counted."""
    try:
        await counted(redis, key, -1, LIMITS[name].window)
    except Exception:
        logger.warning("A preview that didn't start stays counted, Redis failed", exc_info=True)


async def gone_meanwhile(interview_id, preview_id) -> None:
    """Deleted while its preview started: its interview.deleted may have reached rounds before
    these sessions did, so they go here (404)."""
    async with Session() as session:
        if await interviews.get(session, interview_id) is not None:
            return

    await rounds.delete_invite_sessions([preview_id])

    raise HTTPException(status.HTTP_404_NOT_FOUND, "Interview not found")
