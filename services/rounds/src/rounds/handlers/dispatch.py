"""Rounds' events: companies' and accounts' deletions, whose sessions go here (rule 11: deleting
again deletes nothing more, so a redelivery or a repeat is safe, in any order; an error answers
5xx and Pub/Sub delivers the event again)."""

from testee_common.events.deletions import COMPANY_DELETED, INTERVIEW_DELETED, USER_DELETED

from rounds.handlers import company_deleted, interview_deleted, user_deleted

HANDLERS = {
    INTERVIEW_DELETED: interview_deleted.handle,
    COMPANY_DELETED: company_deleted.handle,
    USER_DELETED: user_deleted.handle,
}


async def handle(event_type: str, data: dict) -> None:
    """Other event types aren't rounds' (locally every subscription gets every event)."""
    handler = HANDLERS.get(event_type)

    if handler:
        await handler(data)
