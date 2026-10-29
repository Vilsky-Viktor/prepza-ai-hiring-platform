from enum import StrEnum

# The answer-pattern signals (helpers/answer_patterns.py): each threshold chosen on the eval of
# made-up honest and relaying candidates (evals/README.md, Integrity signals), so it flags at
# most 1% of every honest population at 10, 20 and 30 questions.


class PatternSignal(StrEnum):
    # Nearly the same time on every question, not following length or difficulty.
    TIMING = "timing"
    # Right and wrong answers that don't follow difficulty: hard ones right, easy ones wrong.
    PERSON_FIT = "person_fit"


# Timing: answers given in time it needs, how little their times may vary (the standard deviation
# of their logarithms), and how little they may follow what each question predicts (Spearman's
# rho against its own time, longer by DIFFICULTY_TIME × (1 - difficulty) when that's known).
MIN_TIMED_ANSWERS = 8
MAX_TIME_SPREAD = 0.25
MAX_TIME_RHO = 0.0
DIFFICULTY_TIME = 1.0

# Person-fit: answers to questions with a known difficulty it needs, and the lz index at or
# below which the pattern is unusual (lz is about normal around 0 for honest answers).
MIN_KNOWN_DIFFICULTY = 8
MAX_PERSON_FIT = -4.0
# A difficulty is kept off 0 and 1, so its logit stays finite; Rasch difficulties come from the
# share right as logit(p) ≈ -b / RASCH_SCALE for abilities ~ N(0, 1).
DIFFICULTY_EDGE = 0.03
RASCH_SCALE = 1.18
# Bisection steps for a candidate's ability: far past what the index needs.
ABILITY_STEPS = 50
ABILITY_RANGE = 8.0

# Questions the report suggests asking in a live interview.
FOLLOW_UPS = 3
