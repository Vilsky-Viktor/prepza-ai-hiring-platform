import logging

from prepza_common.ai import ai_usage
from pydantic import ValidationError

from generation.config import settings
from generation.constants.actions import KEY_CHECK_BATCH, QUESTION_VERIFY
from generation.constants.quality import (
    BATCH_RETRY_STATUSES,
    MAX_BATCH_KEY_CHECKS,
    MAX_DIRECT_KEY_CHECKS,
    QualityFlag,
)
from generation.core.db import Session
from generation.helpers.prompts import checker_messages
from generation.integrations import library, openai_batch
from generation.integrations.usage import ai_run
from generation.models.key_checks import KeyCheck as KeyCheckRow
from generation.repositories import key_checks
from generation.schemas.verify import KeyCheck
from generation.services.batch_usage import record_batch
from generation.services.verify import apply_key_check, check_key, key_check_prompt, marked_answer

logger = logging.getLogger(__name__)


def request_body(prompt: str) -> dict:
    return openai_batch.request_body(
        settings.verify_model,
        settings.verify_reasoning_effort,
        checker_messages(prompt),
        KeyCheck,
    )


async def current(check: KeyCheckRow):
    """The question and its context, or None when it was deleted or changed since flagged, its
    key was moved, or it isn't flagged for its key any more (kept, fixed, or this check's result
    was applied already)."""
    context = await library.get_question_context(check.question_id)
    question = await library.get_question_quality(check.question_id)

    if context is None or question is None or question.text != check.question_text:
        return None

    if question.flag != QualityFlag.WRONG_KEY:
        return None

    if check.marked_answer is not None and marked_answer(question) != check.marked_answer:
        return None

    return question, context


async def submit_pending() -> None:
    """Sends the waiting key checks, up to MAX_BATCH_KEY_CHECKS, as one batch; the rest go in
    the next run's."""
    requests = {}
    sent = []
    gone = []

    async with Session() as session:
        waiting = await key_checks.unsent(session, MAX_BATCH_KEY_CHECKS)

    for check in waiting:
        found = await current(check)

        if found is None:
            gone.append(check.question_id)
        else:
            requests[str(check.question_id)] = request_body(
                key_check_prompt(check.question_id, *found)
            )
            sent.append(check)

    if gone:
        await remove(gone)

    if requests:
        try:
            batch_id = await openai_batch.submit(requests)
        except Exception as error:
            await ai_usage.provider_refused(error, KEY_CHECK_BATCH)

            raise

        await set_batch([check.question_id for check in sent], batch_id)
        logger.info("Sent %d key checks in batch %s", len(requests), batch_id)


def parsed(reply: str | None) -> KeyCheck | None:
    """A batch's reply as a key check; None when it has none or it isn't one."""
    try:
        return KeyCheck.model_validate_json(reply) if reply else None
    except ValidationError:
        return None


async def apply_reply(check: KeyCheckRow, reply: str | None) -> None:
    found = await current(check)

    if found is None:
        return

    question, context = found

    result = parsed(reply)

    # A request that failed in the batch is checked right away instead.
    if result is None:
        await check_key(check.question_id, question, context)
    else:
        await apply_key_check(check.question_id, question, context, result)


async def collect_finished() -> None:
    """Applies the results of finished batches. A failed or expired batch's results are applied
    too, and its checks without one go out in the next batch. A finished batch's checks without
    a usable result are checked right away, at most MAX_DIRECT_KEY_CHECKS a run (each at full
    price), so a run ends well within its lock; the rest go out in the next batch."""
    direct = 0

    async with Session() as session:
        batch_ids = await key_checks.sent_batches(session)

    for batch_id in batch_ids:
        status, output_file_id = await openai_batch.status(batch_id)

        if status != "completed" and status not in BATCH_RETRY_STATUSES:
            continue

        async with Session() as session:
            checks = await key_checks.in_batch(session, batch_id)

        replies, used = await openai_batch.results(output_file_id) if output_file_id else ({}, [])
        labels = {
            custom_id: (KEY_CHECK_BATCH, custom_id, f"{QUESTION_VERIFY}:{custom_id}")
            for custom_id, _, _ in used
        }
        await record_batch(batch_id, used, replies, labels)

        for check in checks:
            reply = replies.get(str(check.question_id))

            if parsed(reply) is None:
                if status != "completed" or direct >= MAX_DIRECT_KEY_CHECKS:
                    await set_batch([check.question_id], None)

                    continue

                direct += 1

            try:
                # Applying a reply may call the verifier again, at full price.
                async with ai_run(QUESTION_VERIFY, subject_id=check.question_id):
                    await apply_reply(check, reply)
            except Exception:
                logger.exception("Key check of question %s failed", check.question_id)
                await set_batch([check.question_id], None)

                continue

            await remove([check.question_id])


async def set_batch(question_ids: list, batch_id: str | None) -> None:
    async with Session.begin() as session:
        await key_checks.set_batch(session, question_ids, batch_id)


async def remove(question_ids: list) -> None:
    async with Session.begin() as session:
        await key_checks.remove(session, question_ids)
