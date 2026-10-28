from uuid import UUID

from companies.core.db import Session
from companies.helpers import notifications
from companies.repositories import interviews, invite_progress, invites
from companies.services import outbox as outbox_service


async def undelivered(invite_id: UUID) -> None:
    """Notifications reports a bounced or spam-flagged invite email; safe to repeat. The
    company is told, with the invite marked, in one save."""
    async with Session() as session:
        invite = await invites.get(session, invite_id)
        interview = await interviews.get(session, invite.interview_id) if invite else None

    if invite is None:
        return

    notice = notifications.invite_undelivered(interview, str(invite_id), invite.email, invite.name)

    async with Session.begin() as session:
        await invite_progress.mark_undelivered(session, invite_id, notice)

    await outbox_service.flush_quietly()
