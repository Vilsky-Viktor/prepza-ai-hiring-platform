from datetime import UTC, datetime, timedelta
from time import monotonic

from app.constants.invites import JOB_RUN_SECONDS, REMOVAL_KEEP_DAYS, RETENTION_BATCH
from app.integrations import rounds
from app.storage import accounts, invites, removals


async def replay() -> int:
    """Erases again the candidates companies erased in the last REMOVAL_KEEP_DAYS whose invites
    are back (a database restored or cloned from a backup): their sessions in rounds, the invite,
    and the other services told again. Safe to repeat: an invite that's gone isn't read. Then
    forgets older ones. A batch at a time; none starts JOB_RUN_SECONDS into the run, the rest
    wait for the next. Returns how many it erased again."""
    before = datetime.now(UTC) - timedelta(days=REMOVAL_KEEP_DAYS)
    stop_at = monotonic() + JOB_RUN_SECONDS
    await removals.forget(before)
    # Rows deleted accounts once left behind, blanked but not anonymous: they go too.
    while monotonic() < stop_at and (leftovers := await accounts.blanked_invites(RETENTION_BATCH)):
        await accounts.delete_invites(leftovers)

    erased = 0

    while monotonic() < stop_at and (rows := await removals.restored(before, RETENTION_BATCH)):
        await rounds.delete_invite_sessions([invite.id for invite, _ in rows])

        for invite, company_id in rows:
            await invites.remove(invite, company_id)

        erased += len(rows)

    return erased
