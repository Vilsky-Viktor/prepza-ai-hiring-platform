# A finished batch's calls, recorded once: each priced at batch price for its subject and traced
# to its subject's trace (prepza_common.ai_usage, prepza_common.tracing).
from prepza_common import ai_usage, tracing
from prepza_common.llm import call_cost

from app.constants.quality import BATCH_RECORDED_KEY, BATCH_RECORDED_SECONDS
from app.integrations.redis import get_redis


async def record_batch(
    batch_id: str,
    used: list[tuple[str, str, dict]],
    replies: dict[str, str | None],
    labels: dict[str, tuple[str, str, str]],
) -> None:
    """Each request's usage (`used`: custom id, model, usage), once a batch: `labels` gives each
    custom id its action, its subject's id and the trace it joins."""
    key = f"{BATCH_RECORDED_KEY}:{batch_id}"

    if not used or not await get_redis().set(key, 1, nx=True, ex=BATCH_RECORDED_SECONDS):
        return

    for custom_id, model, usage in used:
        if custom_id not in labels:
            continue

        action, subject_id, seed = labels[custom_id]
        await ai_usage.record(action, model, usage, batch=True, subject_id=subject_id)
        tracing.traced_call(
            action,
            [action, subject_id],
            seed,
            model,
            usage,
            call_cost(model, usage, batch=True),
            replies.get(custom_id),
        )
