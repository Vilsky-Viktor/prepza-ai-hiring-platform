# What billing's history says a movement was: a top-up, or a candidate's charge.
class Reason:
    TOPUP = "topup"
    CANDIDATE = "candidate"


# How often a new company's welcome credits are asked for before the company is removed again.
WELCOME_ATTEMPTS = 3
# The first wait before asking again, doubling after each try (with jitter): the owner is waiting.
WELCOME_FIRST_WAIT_SECONDS = 0.2
