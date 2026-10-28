import uuid

from prepza_common.events import outbox
from prepza_common.events.notifications import NOTIFICATION_REQUESTED, NotificationKind
from sqlalchemy import select, update

from library.constants.quality import COPY_FIX_BATCH
from library.core.db import Session
from library.helpers.notifications import question_notification
from library.models.outbox import OutboxEvent
from library.models.sets import Question, QuestionSet, Topic
from library.repositories import quality


def set_query(question_id: uuid.UUID):
    return (
        select(QuestionSet)
        .join(Topic, Topic.set_id == QuestionSet.id)
        .join(Question, Question.topic_id == Topic.id)
        .where(Question.id == question_id)
    )


def topic_query(question_id: uuid.UUID):
    return (
        select(Topic.title)
        .join(Question, Question.topic_id == Topic.id)
        .where(Question.id == question_id)
    )


def notify_fixed(session, question_id: uuid.UUID, question_set, topic: str | None) -> None:
    """Tells the set's owner, in `session`, that a question in it was fixed: a company only."""
    notification = question_notification(question_set, topic, NotificationKind.QUESTION_FIXED)

    if notification is not None:
        outbox.add(session, OutboxEvent, NOTIFICATION_REQUESTED, notification)


async def fix_copies(question_id: uuid.UUID, old_text: str, old_options: list[dict]) -> int:
    """Up to COPY_FIX_BATCH copies of a fixed bank question that still hold its old content
    (not one a company changed, nor one fixed on its own) get its current content, each kept as
    a fixed revision and its company told; how many. Copies another run holds are skipped, and
    a fixed copy no longer matches, so running it again fixes nothing twice."""
    async with Session() as session:
        original = await session.get(Question, question_id)

        if original is None:
            return 0

        copies = list(
            await session.scalars(
                select(Question.id)
                .where(
                    Question.source_question_id == question_id,
                    Question.text == old_text,
                    Question.options == old_options,
                )
                .limit(COPY_FIX_BATCH)
                .with_for_update(skip_locked=True)
            )
        )

        for copy_id in copies:
            await quality.archive(session, copy_id, fixed=True)
            notify_fixed(
                session,
                copy_id,
                await session.scalar(set_query(copy_id)),
                await session.scalar(topic_query(copy_id)),
            )

        if copies:
            await session.execute(
                update(Question)
                .where(Question.id.in_(copies))
                .values(text=original.text, options=original.options)
            )

        await session.commit()

        return len(copies)
