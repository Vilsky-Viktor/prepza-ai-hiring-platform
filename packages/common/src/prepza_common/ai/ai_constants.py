# What AI costs and how each call is recorded (ai_usage.record): billing stores every call and
# shows the admin zone's "AI costs" tab.
from enum import StrEnum

# USD per million tokens: input, cached input and output (OpenAI's pricing page, October 2026).
# An embedding model reads only. The one place for prices: every service's cost, the "AI used"
# log line and the offline tests' report come from here (llm.call_cost).
MODEL_PRICES = {
    "gpt-6-luna": (0.10, 0.01, 0.50),
    "gpt-6.1-sol": (2.00, 0.20, 10.00),
    "gpt-6-astra": (10.00, 1.00, 50.00),
    "text-embedding-3-small": (0.02, 0.02, 0.0),
}
# USD per minute of audio turned into text.
TRANSCRIPTION_PRICES = {
    "gpt-4o-mini-transcribe": 0.003,
    "gpt-4o-transcribe": 0.006,
}
# The Batch API charges this share of the usual price.
BATCH_SHARE = 0.5

# The events billing stores, on the events topic; nothing else consumes them.
AI_USED = "ai.used"
LIMIT_HIT = "limit.hit"
# A record's publish is tried this many times before it's given up (and logged).
RECORD_ATTEMPTS = 3


class Outcome(StrEnum):
    OK = "ok"
    # Cancelled or stopped before its answer was whole.
    CUT = "cut"
    FAILED = "failed"


# Every kind of AI call, by the service that makes it. Services that made AI calls before but no
# longer do, whose recorded calls billing keeps (rounds made the help chat's until 2026-10-29).
PAST_AI_SERVICES = {"rounds"}
ACTIONS = {
    "interview_generation": "generation",
    "template_generation": "generation",
    "question_regeneration": "generation",
    "template_question_regeneration": "generation",
    "sample_key_check": "generation",
    "question_verify": "generation",
    "key_check_batch": "generation",
    "embeddings": "generation",
    "news_translation": "generation",
    "campaign_translation": "generation",
    "quality_patterns": "generation",
    "code_tags": "generation",
    "assistant_message": "assistant",
    "assistant_title": "assistant",
    "transcription": "assistant",
    "help_chat": "assistant",
}
# Work prepza does for itself: billing counts a call without a company as prepza's when it's one
# of these, and as someone's without a company otherwise. A call made for a company is always the
# company's (an interview's embeddings or sample key check).
PREPZA_ACTIONS = {
    "template_generation",
    "sample_key_check",
    "template_question_regeneration",
    "question_verify",
    "key_check_batch",
    "embeddings",
    "news_translation",
    "campaign_translation",
    "quality_patterns",
    "code_tags",
}


class Category(StrEnum):
    """Who a call was for, as billing decides it when storing the call."""

    PAID = "paid"
    UNPAID = "unpaid"
    NO_COMPANY = "no_company"
    PREPZA = "prepza"


# The daily AI spend cap for unpaid companies and people without a company: what they spent
# today (UTC), in micro-dollars, under this key and the date. Billing adds each call as it stores
# it; the services refuse AI calls for them once it reaches the AI_SPEND_UNPAID_DAY limit.
UNPAID_SPEND_KEY = "spend:ai:unpaid"
# Kept a little past its day, so the tab can still read yesterday's late calls.
UNPAID_SPEND_KEY_SECONDS = 2 * 24 * 60 * 60
# The share of the cap that sends the early alert, so it can be raised before anyone is refused.
UNPAID_SPEND_ALERT_SHARE = 0.8
MICRO = 1_000_000
AI_PAUSED_TODAY = (
    "AI features are paused for today. They're back tomorrow, or right away for companies that "
    "have topped up."
)
