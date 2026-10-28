# What every key check shares: the checker's role (the system message of the verifier's check,
# the blind confirmation and the self-check) and what each kind of question's key is.
# Who checks a key, in the system message of every check below (rule 19: generic to
# prepza's work, never one field).
VERIFIER_ROLE = (
    "You are a subject-matter reviewer who checks the answer keys of multiple-choice "
    "questions in skills tests, in any field, on the facts alone."
)

# The key check is told the question's kind: a single-answer question has exactly one correct
# option, a select-all-that-apply one 2 or 3 (prepza_common.ai.multi_answer).
SINGLE_ANSWER_KEY = """This is a single-answer question. Return correct_indexes: a list with the
number of the one option that is correct for the question exactly as written. Return null when
none of the options is correct, or when more than one could be defended as correct."""

MULTI_ANSWER_KEY = """This is a select-all-that-apply question: 2 or 3 of its 4 options are
correct, never all of them. Judge each option on its own. Return correct_indexes: the numbers of
every option that is correct for the question exactly as written. Return null when fewer than two
or all four are correct, or when any option could be defended both as correct and as wrong."""
