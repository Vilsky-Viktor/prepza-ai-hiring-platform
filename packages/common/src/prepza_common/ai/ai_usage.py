"""Recording every AI call: what it was for, its tokens and its cost, worked out here from
ai_constants' prices. Each call is one log line (the prepza_ai_spend metric and the AI spend
alert) and one event billing stores for the admin zone's "AI costs" tab. Needs the package's `llm`
extra."""

import logging

import openai
from prepza_common.ai.ai_constants import ACTIONS, AI_USED, RECORD_ATTEMPTS, Outcome
from prepza_common.ai.llm import call_cost, transcription_cost
from prepza_common.config.event_constants import PUBLISH_IN_REQUEST_TIMEOUT_SECONDS
from prepza_common.events.pubsub import publish_retried
from prepza_common.limits.limits import record_hit

logger = logging.getLogger(__name__)

QUOTA_CODE = "insufficient_quota"


async def record(
    action: str,
    model: str,
    usage: dict | None = None,
    *,
    audio_seconds: float = 0.0,
    batch: bool = False,
    company_id: object | None = None,
    user_id: str | None = None,
    subject_id: object | None = None,
    outcome: Outcome = Outcome.OK,
) -> None:
    """Records one AI call (or one run's calls of a model) after it answered, failed or was cut
    short. `usage` is LangChain's usage metadata (input_tokens, output_tokens and
    input_token_details.cache_read), estimated for a call that reported none; transcription
    gives `audio_seconds` instead. Never raises."""
    usage = usage or {}
    cached = (usage.get("input_token_details") or {}).get("cache_read", 0) or 0

    if audio_seconds:
        cost = transcription_cost(model, audio_seconds)
    else:
        cost = call_cost(model, usage, batch)

    if cost is None:
        logger.warning("No price for model %s; its cost is recorded as 0", model)

    data = {
        "action": action,
        "service": ACTIONS[action],
        "model": model,
        "input_tokens": usage.get("input_tokens", 0),
        "cached_input_tokens": cached,
        "output_tokens": usage.get("output_tokens", 0),
        "audio_seconds": audio_seconds,
        "cost_usd": cost or 0.0,
        "company_id": str(company_id) if company_id else None,
        "user_id": user_id,
        "subject_id": str(subject_id) if subject_id else None,
        "outcome": outcome,
    }
    logger.info(
        "AI used: action=%s model=%s input=%d cached=%d output=%d audio=%.1f outcome=%s cost=$%.6f",
        action,
        model,
        data["input_tokens"],
        cached,
        data["output_tokens"],
        audio_seconds,
        outcome,
        data["cost_usd"],
    )
    await publish_retried(AI_USED, data, RECORD_ATTEMPTS, PUBLISH_IN_REQUEST_TIMEOUT_SECONDS)


async def provider_refused(
    error: BaseException,
    what: str,
    company_id: object | None = None,
    user_id: str | None = None,
) -> None:
    """Records OpenAI refusing a call for its limits: its rate limit, or the account out of
    money (`insufficient_quota`), which stops all AI and is logged as an error at once. Other
    errors aren't limit hits and record nothing."""
    if not isinstance(error, openai.RateLimitError):
        return

    name = "OPENAI_RATE_LIMIT"

    if error.code == QUOTA_CODE:
        name = "OPENAI_QUOTA"
        logger.error("OpenAI quota exhausted: every AI call fails until the account is topped up")

    who = {"company_id": company_id, "user_id": user_id}
    await record_hit(name, kind="provider:openai", scope="everyone", what=what, **who)
