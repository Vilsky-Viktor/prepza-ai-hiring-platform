# What billing's history says a movement was: a top-up, or a candidate's charge.
class Reason:
    TOPUP = "topup"
    CANDIDATE = "candidate"


# How often a new company's welcome credits are asked for before the company is removed again.
WELCOME_ATTEMPTS = 3
# The first wait before asking again, doubling after each try (with jitter): the owner is waiting.
WELCOME_FIRST_WAIT_SECONDS = 0.2
# Billing reads a failed payment from Paddle in at most about 9 seconds (two bounded reads, a
# second apart); a little longer than that here.
PAYMENT_FAILURE_TIMEOUT_SECONDS = 10
