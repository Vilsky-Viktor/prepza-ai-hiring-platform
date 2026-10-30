import uuid
from datetime import datetime

from prepza_common.config.constants import VOICE_READING_SECONDS
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from rounds.constants.rounds import INTERVIEW_TIME_MARGIN

# Candidate interviews (all sessions of an invite) still in progress past their deadline: the
# start plus every question's seconds (their own times add up to the questions times the
# average) and, taken by voice, each question's reading allowance, plus the margin. Sessions from before every interview
# was timed have no seconds and never expire. Only interviews with a running section are looked
# at, through the partial index on them (ix_sessions_running_invite); the status is written out,
# as the index's condition is, so the planner can always use it.
EXPIRED_SQL = text(
    """
    SELECT candidate_invite_id FROM sessions
    WHERE candidate_invite_id IN (
        SELECT candidate_invite_id FROM sessions
        WHERE status = 'in_progress'
            AND (CAST(:invite_id AS uuid) IS NULL OR candidate_invite_id = CAST(:invite_id AS uuid))
    )
    GROUP BY candidate_invite_id
    HAVING bool_and(question_seconds IS NOT NULL)
        AND min(started_at) + make_interval(
            secs => sum(
                jsonb_array_length(questions)
                * (question_seconds + CASE WHEN voice THEN :reading ELSE 0 END)
            ) * (1 + :margin)
        ) < :now
    LIMIT :limit
    """
)


async def expired_invites(
    session: AsyncSession, now: datetime, limit: int, invite_id: uuid.UUID | None = None
) -> list[uuid.UUID]:
    """Invites whose interview ran out of time; only `invite_id` when given."""
    params = {
        "invite_id": str(invite_id) if invite_id else None,
        "margin": INTERVIEW_TIME_MARGIN,
        "reading": VOICE_READING_SECONDS,
        "now": now,
        "limit": limit,
    }

    return list(await session.scalars(EXPIRED_SQL, params))
