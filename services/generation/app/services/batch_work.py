# Work that waits on nobody goes through OpenAI's Batch API at half price (.claude/rules/ai.md):
# translations of news posts and campaigns, new options for a question and rewritten questions.
# It's queued (`queue`), sent every 10 minutes with the key checks (`submit_pending`), and each
# reply moves its piece on (`collect_finished`): to its result, saved where it belongs, or to its
# next call, sent in the next batch. Every step is idempotent: a batch read twice moves nothing
# twice, and a subject changed since it was queued (an edited post, a question kept or replaced)
# drops its result.
import logging
import uuid

from app.constants.actions import CAMPAIGN_TRANSLATION, NEWS_TRANSLATION, QUESTION_VERIFY
from app.constants.batch_work import MAX_BATCH_WORK, BatchKind, BatchStep
from app.constants.quality import BATCH_RETRY_STATUSES
from app.integrations import library, notifications, openai_batch
from app.integrations.usage import ai_run
from app.models.batch_work import BatchWork
from app.schemas.campaigns import CampaignSource
from app.schemas.news import NewsSource
from app.schemas.regenerate import QuestionContext, RegeneratedQuestion
from app.services.batch_steps import advance, body_for
from app.services.batch_usage import record_batch
from app.storage import batch_work

logger = logging.getLogger(__name__)

ACTIONS = {
    BatchKind.NEWS: NEWS_TRANSLATION,
    BatchKind.CAMPAIGN: CAMPAIGN_TRANSLATION,
    BatchKind.NEW_OPTIONS: QUESTION_VERIFY,
    BatchKind.REWRITE: QUESTION_VERIFY,
}


async def queue(kind: str, subject_id: uuid.UUID, step: str, payload: dict, key: str = "") -> None:
    """Queues a piece of work at its first step; one already waiting for the same subject (and
    language) keeps its place."""
    body = body_for(kind, step, payload)
    await batch_work.add(kind, subject_id, key, step, payload, body)


async def queue_rewrite(
    question_id: uuid.UUID, context: QuestionContext, text: str, reasons: list[str]
) -> None:
    """A new question in place of `text`, written to avoid what users reported (`reasons`)."""
    payload = question_payload(context, text, reasons)
    await queue(BatchKind.REWRITE, question_id, BatchStep.QUESTION, payload)


async def queue_new_options(
    question_id: uuid.UUID, context: QuestionContext, text: str, reasons: list[str]
) -> None:
    """New options for the question `text`; an ambiguous one is rewritten instead."""
    payload = question_payload(context, text, reasons)
    await queue(BatchKind.NEW_OPTIONS, question_id, BatchStep.OPTIONS, payload)


def question_payload(context: QuestionContext, text: str, reasons: list[str]) -> dict:
    """What a question's steps need: its context, its text when flagged (a result for a
    question changed since is dropped), the texts a new one must differ from."""
    return {
        # Without its owner: no one's id waits in the table.
        "context": context.model_copy(update={"owner_id": ""}).model_dump(mode="json"),
        "flagged": text,
        "text": text,
        "reasons": reasons,
        "existing": list(context.existing),
    }


async def submit_pending() -> None:
    """Sends the waiting pieces, up to MAX_BATCH_WORK, as one batch."""
    waiting = await batch_work.unsent(MAX_BATCH_WORK)

    if not waiting:
        return

    batch_id = await openai_batch.submit({str(work.id): work.body for work in waiting})
    await batch_work.set_batch([work.id for work in waiting], batch_id)
    logger.info("Sent %d pieces of batch work in batch %s", len(waiting), batch_id)


async def collect_finished() -> None:
    """Moves on every piece of a finished batch. A failed or expired batch's pieces without a
    reply go out again in the next batch."""
    for batch_id in await batch_work.sent_batches():
        status, output_file_id = await openai_batch.status(batch_id)

        if status != "completed" and status not in BATCH_RETRY_STATUSES:
            continue

        pieces = await batch_work.in_batch(batch_id)
        replies, used = await openai_batch.results(output_file_id) if output_file_id else ({}, [])
        labels = {
            str(work.id): (
                ACTIONS[work.kind],
                str(work.subject_id),
                f"{ACTIONS[work.kind]}:{work.subject_id}",
            )
            for work in pieces
        }
        await record_batch(batch_id, used, replies, labels)

        for work in pieces:
            if str(work.id) not in replies and status != "completed":
                await batch_work.set_batch([work.id], None)

                continue

            try:
                async with ai_run(ACTIONS[work.kind], subject_id=work.subject_id):
                    await move_on(work, batch_id, replies.get(str(work.id)))
            except Exception:
                # Sent again in the next batch; a failing subject gives up after its attempts.
                logger.exception("Batch work %s on %s failed", work.kind, work.subject_id)
                await batch_work.set_batch([work.id], None)


async def move_on(work: BatchWork, batch_id: str, reply: str | None) -> None:
    """The piece's result saved, or its next call queued, or the piece given up."""
    found = await advance(work.kind, work.step, work.attempt, work.payload, reply)

    if found.give_up:
        logger.warning("Batch work %s on %s gave up", work.kind, work.subject_id)
        await batch_work.remove([work.id])

        return

    if found.result is None:
        body = body_for(work.kind, found.step, found.payload)
        await batch_work.next_step(
            work.id, batch_id, found.step, work.attempt + 1, found.payload, body
        )

        return

    await save(work, found.result)
    await batch_work.remove([work.id])


async def save(work: BatchWork, result) -> None:
    """A translation into its post's or campaign's language (dropped there if the text changed
    since); a question's new text and options, only while it's still the one flagged."""
    if work.kind == BatchKind.NEWS:
        source = NewsSource(**work.payload["source"])
        await library.save_news_translations(work.subject_id, source, {work.key: result})

        return

    if work.kind == BatchKind.CAMPAIGN:
        source = CampaignSource(**work.payload["source"])
        await notifications.save_campaign_translations(work.subject_id, source, {work.key: result})

        return

    question = await library.get_question_quality(work.subject_id)

    # Kept, replaced or edited since it was flagged.
    if question is None or question.flag is None or question.text != work.payload["flagged"]:
        return

    text, options = result
    await library.replace_question(work.subject_id, RegeneratedQuestion(text=text, options=options))
