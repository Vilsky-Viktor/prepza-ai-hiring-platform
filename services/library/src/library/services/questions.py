import uuid

from prepza_common.ai.multi_answer import is_multi
from prepza_common.events.notifications import NotificationKind

from library.constants.events import QUESTION_FIXED
from library.constants.sets import SetKind
from library.core.db import Session
from library.models.feedback import QuestionReport
from library.models.sets import QuestionSet
from library.repositories import feedback, outbox, preparations, quality
from library.schemas.preparations import QuestionText
from library.services import outbox as outbox_service
from library.services.notices import tell_owner


async def topic_questions(topic_id: uuid.UUID) -> tuple[QuestionSet, list[QuestionText]] | None:
    """A topic's set, and its questions with their options and feedback counts; None when
    there's no such topic."""
    async with Session() as session:
        found = await preparations.get_topic_with_question_texts(session, topic_id)

        if found is None:
            return None

        question_set, topic = found
        stats = await feedback.question_stats(
            session, [question.id for question in topic.questions]
        )

    return question_set, [
        QuestionText(
            id=question.id,
            text=question.text,
            options=question.options,
            multi=is_multi(question.options),
            **stats.get(question.id, {}),
        )
        for question in topic.questions
    ]


async def reports(
    question_id: uuid.UUID, set_id: uuid.UUID, offset: int, limit: int, template: bool = False
) -> list[QuestionReport] | None:
    """A question's reports, newest first; None when it isn't in the set `set_id` (or, with
    `template`, that set isn't a template)."""
    async with Session() as session:
        question_set = await preparations.get_for_question(session, question_id)

        if question_set is None or question_set.id != set_id:
            return None

        if template and question_set.kind != SetKind.TEMPLATE:
            return None

        return await feedback.list_reports(session, question_id, offset, limit)


async def replace(question_id: uuid.UUID, text: str, options: list[dict]) -> None:
    """New content in the same slot, for candidates who start after it. The old content and its
    feedback are kept as a revision.

    Replacing a flagged question fixes it, and its set's owner hears of that. A fixed bank
    question's unchanged copies in companies' tests are fixed after it, a batch at a time
    (question.fixed, services/copy_fixes.py), and each company hears of it. One save.
    """
    async with Session.begin() as session:
        flagged = await quality.current_flag(session, question_id) is not None
        old = await preparations.question(session, question_id)
        before = {"text": old.text, "options": old.options} if old else None
        await quality.archive(session, question_id, fixed=flagged)
        await preparations.set_content(session, question_id, text, options)

        if flagged and before is not None:
            await tell_owner(session, question_id, NotificationKind.QUESTION_FIXED)
            outbox.add(session, QUESTION_FIXED, {"question_id": str(question_id), **before})

    await outbox_service.flush_quietly()
