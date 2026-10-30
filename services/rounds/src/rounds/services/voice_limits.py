from prepza_common.ai.ai_cap import refuse_if_capped
from prepza_common.limits.rate_limit import hit

from rounds.integrations.redis import get_redis
from rounds.models.sessions import Session


async def check_answer(row: Session) -> None:
    """Counts one spoken answer, refused (429) over the candidate's hourly limit or their
    company's daily one; a company member's preview also once today's unpaid AI spend cap is
    reached (503). A candidate's interview is paid for by its invite, so only the limits stop
    it. Spend limits fail closed: with Redis down, the answer is refused and the candidate taps."""
    redis = get_redis()
    who = {"company_id": row.company_id, "user_id": row.user_id}

    if row.preview:
        await refuse_if_capped(redis, **who)

    await hit(redis, f"rate:voice:answers:user:{row.user_id}", "VOICE_ANSWERS_PER_USER_HOUR", **who)
    key = f"rate:voice:answers:company:{row.company_id}"
    await hit(redis, key, "VOICE_ANSWERS_PER_COMPANY_DAY", **who)


async def check_clip(row: Session) -> None:
    """Counts one text read aloud for the first time, as check_answer does, over the company's
    and everyone's daily limits."""
    redis = get_redis()
    who = {"company_id": row.company_id, "user_id": row.user_id}

    if row.preview:
        await refuse_if_capped(redis, **who)

    key = f"rate:voice:clips:company:{row.company_id}"
    await hit(redis, key, "VOICE_CLIPS_PER_COMPANY_DAY", **who)
    await hit(redis, "rate:voice:clips:all", "VOICE_CLIPS_PER_DAY", **who)
