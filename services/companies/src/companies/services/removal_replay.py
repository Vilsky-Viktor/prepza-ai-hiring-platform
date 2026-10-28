from datetime import UTC, datetime, timedelta
from time import monotonic

from companies.constants.invites import JOB_RUN_SECONDS, REMOVAL_KEEP_DAYS, RETENTION_BATCH
from companies.core.db import Session
from companies.integrations import rounds
from companies.repositories import accounts, invites, removals


async def blanked() -> list:
    async with Session() as session:
        return await accounts.blanked_invites(session, RETENTION_BATCH)


async def restored(before: datetime) -> list[tuple]:
    async with Session() as session:
        return await removals.restored(session, before, RETENTION_BATCH)


async def replay() -> int:
    """Erases again the candidates companies erased in the last REMOVAL_KEEP_DAYS whose invites
    are back (a database restored or cloned from a backup): their sessions in rounds, the invite,
    and the other services told again. Safe to repeat: an invite that's gone isn't read. Then
    forgets older ones. A batch at a time; none starts JOB_RUN_SECONDS into the run, the rest
    wait for the next. Returns how many it erased again."""
    before = datetime.now(UTC) - timedelta(days=REMOVAL_KEEP_DAYS)
    stop_at = monotonic() + JOB_RUN_SECONDS
    await removals.forget(Session, before)
    # Rows deleted accounts once left behind, blanked but not anonymous: they go too.
    while monotonic() < stop_at and (leftovers := await blanked()):
        async with Session.begin() as session:
            await accounts.delete_invites(session, leftovers)

    erased = 0

    while monotonic() < stop_at and (rows := await restored(before)):
        await rounds.delete_invite_sessions([invite.id for invite, _ in rows])

        async with Session.begin() as session:
            for invite, company_id in rows:
                await invites.remove(session, invite, company_id)

        erased += len(rows)

    return erased
