# A superadmin adds this many questions to every topic of a template by default, in steps of
# ADDED_QUESTIONS_STEP, at most MAX_ADDED_QUESTIONS a run: a whole new topic's worth, a ceiling
# on one click's AI spend. A third of them go to practice and the rest to companies, as in a new
# template (library's constants/sets.py: 30 practice, 60 company), hence the steps of 3.
DEFAULT_ADDED_QUESTIONS = 30
ADDED_QUESTIONS_STEP = 3
MAX_ADDED_QUESTIONS = 90

ADDITION_RUNNING = "Questions are already being added to this template."
NOTHING_TO_TOP_UP = "Every topic already has its practice and company questions."
ADDED_QUESTIONS_INVALID = (
    f"Choose a number of questions from {ADDED_QUESTIONS_STEP} to {MAX_ADDED_QUESTIONS}, "
    f"in steps of {ADDED_QUESTIONS_STEP}."
)
