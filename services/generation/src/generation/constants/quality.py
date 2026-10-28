from enum import StrEnum


class QualityFlag(StrEnum):
    """Why the library sent a question to the verifier; mirrors the library's flags."""

    WRONG_KEY = "wrong_key"
    REWRITE = "rewrite"
    WEAK_OPTIONS = "weak_options"


# A batch that ended this way has its results applied, and its checks without one sent again.
BATCH_RETRY_STATUSES = ("failed", "expired", "cancelled")
# Key checks a finished batch left without a result that one run checks right away, at full
# price; the rest go out in the next batch.
MAX_DIRECT_KEY_CHECKS = 20
# Key checks sent in one batch (each is looked up in the library first).
MAX_BATCH_KEY_CHECKS = 500
# One key-check run at a time: a slow run isn't joined by the next scheduled one. The lock
# outlasts a run's longest time (the worker's 30-minute request timeout).
KEY_CHECK_LOCK_KEY = "lock:key-check-batches"
KEY_CHECK_LOCK_SECONDS = 30 * 60
# A new test's or template's answer keys checked by the verifier before it's ready: this many
# random questions a topic (about $0.001 each).
KEY_CHECKS_PER_TOPIC = 1
# Verifier jobs a day, for everyone together (the DAILY_VERIFY_LIMIT limit): a ceiling on what
# flags can spend on rewrites (a few cents each). A superadmin's "Fix now" isn't counted.
VERIFY_BUDGET_KEY = "budget:verify"
VERIFY_PAUSED = "Today's limit for question checks is reached; the question is checked later."
# A finished batch's usage is recorded once: a run that stopped halfway reads the batch again.
BATCH_RECORDED_KEY = "recorded:key-check-batch"
BATCH_RECORDED_SECONDS = 7 * 24 * 60 * 60
