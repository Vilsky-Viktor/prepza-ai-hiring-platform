import logging
from datetime import UTC, datetime, timedelta
from time import monotonic

from app.constants.audit import AUDIT_RETENTION_DAYS
from app.constants.invites import CANDIDATE_RETENTION_DAYS, JOB_RUN_SECONDS, RETENTION_BATCH
from app.integrations import rounds
from app.services.candidate_billing import release_unfinished
from app.storage import accounts, audit

logger = logging.getLogger(__name__)


async def delete_expired_candidates() -> int:
    """Candidate invites older than CANDIDATE_RETENTION_DAYS go, in batches, with the candidates'
    answers, timings and page-leave signals in rounds, and any credits still held for them.
    Rounds and billing first, so a failure is retried whole the next run. No batch starts
    JOB_RUN_SECONDS into the run: the rest go the next day."""
    before = datetime.now(UTC) - timedelta(days=CANDIDATE_RETENTION_DAYS)
    stop_at = monotonic() + JOB_RUN_SECONDS
    count = 0

    while monotonic() < stop_at and (
        rows := await accounts.expired_invites(before, RETENTION_BATCH)
    ):
        invite_ids = [row[0] for row in rows]
        await rounds.delete_invite_sessions(invite_ids)
        await release_unfinished([row[1:] for row in rows])
        await accounts.delete_invites(invite_ids)
        count += len(rows)

    return count


async def delete_old_audit_events() -> int:
    """Audit events older than AUDIT_RETENTION_DAYS go."""
    before = datetime.now(UTC) - timedelta(days=AUDIT_RETENTION_DAYS)

    return await audit.delete_before(before)
