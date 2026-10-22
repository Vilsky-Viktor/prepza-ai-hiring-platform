import logging

from prepza_common import ai_usage, tracing
from prepza_common.llm import call_cost
from pydantic import ValidationError

from app.config.settings import settings
from app.constants.actions import KEY_CHECK_BATCH, QUESTION_VERIFY
from app.constants.generation import MAX_OUTPUT_TOKENS
from app.constants.quality import (
    BATCH_RECORDED_KEY,
    BATCH_RECORDED_SECONDS,
    BATCH_RETRY_STATUSES,
    MAX_BATCH_KEY_CHECKS,
    MAX_DIRECT_KEY_CHECKS,
    QualityFlag,
)
from app.integrations import library, openai_batch
from app.integrations.redis import get_redis
from app.integrations.usage import ai_run
from app.models.key_checks import KeyCheck as KeyCheckRow
from app.prompts.verify import VERIFIER_ROLE
from app.schemas.verify import KeyCheck
from app.services.verify import apply_key_check, check_key, key_check_prompt, marked_answer
from app.storage import key_checks

logger = logging.getLogger(__name__)


def request_body(prompt: str) -> dict:
    return {
        "model": settings.verify_model,
        "reasoning_effort": settings.verify_reasoning_effort,
        "max_completion_tokens": MAX_OUTPUT_TOKENS,
        "messages": [
            {"role": "system", "content": VERIFIER_ROLE},
            {"role": "user", "content": prompt},
        ],
        # Strict, as with_structured_output asks for the checks made at once.
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "key_check",
                "strict": True,
                "schema": {**KeyCheck.model_json_schema(), "additionalProperties": False},
            },
        },
    }


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

    for check in await key_checks.unsent(MAX_BATCH_KEY_CHECKS):
        found = await current(check)

        if found is None:
            gone.append(check.question_id)
        else:
            requests[str(check.question_id)] = request_body(
                key_check_prompt(check.question_id, *found)
            )
            sent.append(check)

    if gone:
        await key_checks.remove(gone)

    if requests:
        try:
            batch_id = await openai_batch.submit(requests)
        except Exception as error:
            await ai_usage.provider_refused(error, KEY_CHECK_BATCH)

            raise

        await key_checks.set_batch([check.question_id for check in sent], batch_id)
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


async def record_batch(
    batch_id: str, used: list[tuple[str, str, dict]], replies: dict[str, str | None]
) -> None:
    """Each request's usage, once a batch: priced for its question, and traced to the question's
    verify trace (the one its direct checks use)."""
    key = f"{BATCH_RECORDED_KEY}:{batch_id}"

    if not used or not await get_redis().set(key, 1, nx=True, ex=BATCH_RECORDED_SECONDS):
        return

    for question_id, model, usage in used:
        await ai_usage.record(KEY_CHECK_BATCH, model, usage, batch=True, subject_id=question_id)
        tracing.traced_call(
            KEY_CHECK_BATCH,
            [KEY_CHECK_BATCH, question_id],
            f"{QUESTION_VERIFY}:{question_id}",
            model,
            usage,
            call_cost(model, usage, batch=True),
            replies.get(question_id),
        )


async def collect_finished() -> None:
    """Applies the results of finished batches. A failed or expired batch's results are applied
    too, and its checks without one go out in the next batch. A finished batch's checks without
    a usable result are checked right away, at most MAX_DIRECT_KEY_CHECKS a run (each at full
    price), so a run ends well within its lock; the rest go out in the next batch."""
    direct = 0

    for batch_id in await key_checks.sent_batches():
        status, output_file_id = await openai_batch.status(batch_id)

        if status != "completed" and status not in BATCH_RETRY_STATUSES:
            continue

        checks = await key_checks.in_batch(batch_id)
        replies, used = await openai_batch.results(output_file_id) if output_file_id else ({}, [])
        await record_batch(batch_id, used, replies)

        for check in checks:
            reply = replies.get(str(check.question_id))

            if parsed(reply) is None:
                if status != "completed" or direct >= MAX_DIRECT_KEY_CHECKS:
                    await key_checks.set_batch([check.question_id], None)

                    continue

                direct += 1

            try:
                # Applying a reply may call the verifier again, at full price.
                async with ai_run(QUESTION_VERIFY, subject_id=check.question_id):
                    await apply_reply(check, reply)
            except Exception:
                logger.exception("Key check of question %s failed", check.question_id)
                await key_checks.set_batch([check.question_id], None)

                continue

            await key_checks.remove([check.question_id])
