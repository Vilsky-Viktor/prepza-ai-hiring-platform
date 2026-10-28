import uuid

from prepza_common.events.notifications import NotificationKind
from sqlalchemy.ext.asyncio import AsyncSession

from library.helpers.notifications import question_notification
from library.repositories import outbox, preparations


async def owner_notice(
    session: AsyncSession, question_id: uuid.UUID, kind: NotificationKind
) -> dict | None:
    """The notification the owner of the question's set gets, naming its topic; None for a
    template's question (question_notification)."""
    question_set = await preparations.get_for_question(session, question_id)
    topic = await preparations.topic_of_question(session, question_id)

    return question_notification(question_set, topic, kind)


async def tell_owner(session: AsyncSession, question_id: uuid.UUID, kind: NotificationKind) -> None:
    """Tells the set's owner, in `session`, of a change to a question in it: a company only."""
    notice = await owner_notice(session, question_id, kind)

    if notice is not None:
        outbox.notify(session, notice)
