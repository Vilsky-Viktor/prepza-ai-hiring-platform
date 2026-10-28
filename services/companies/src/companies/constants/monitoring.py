from enum import StrEnum

# The monitoring plan's pass-rate trigger (internal_docs/compliance/post-market-monitoring-plan.md,
# section 3): an interview whose pass rate is below LOW or above HIGH percent, once at least
# MIN_FINISHED candidates finished it, needs a look.
PASS_RATE_LOW = 10
PASS_RATE_HIGH = 95
PASS_RATE_MIN_FINISHED = 20


# How the superadmin's pass rates are listed: lowest pass rate first, or most finished first.
class PassRateSort(StrEnum):
    PASS_RATE = "pass_rate"
    FINISHED = "finished"
