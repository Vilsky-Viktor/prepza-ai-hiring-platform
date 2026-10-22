from datetime import UTC, datetime, timedelta

from app.constants.invites import REMOVAL_KEEP_DAYS
from app.integrations import rounds
from app.storage import invites, removals


async def replay() -> int:
    """Erases again the candidates companies erased in the last REMOVAL_KEEP_DAYS whose invites
    are back (a database restored or cloned from a backup): their sessions in rounds, the invite,
    and the other services told again. Safe to repeat: an invite that's gone is skipped. Then
    forgets older ones. Returns how many it erased again."""
    before = datetime.now(UTC) - timedelta(days=REMOVAL_KEEP_DAYS)
    await removals.forget(before)
    erased = 0

    for removal in await removals.since(before):
        invite = await invites.get(removal.invite_id)

        if invite is None:
            continue

        await rounds.delete_invite_sessions([invite.id])
        await invites.remove(invite, removal.company_id)
        erased += 1

    return erased
