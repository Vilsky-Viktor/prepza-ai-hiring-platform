# Who checks a key, in the system message of every check below (rule 19: generic to
# prepza's work, never one field).
VERIFIER_ROLE = (
    "You are a subject-matter reviewer who checks the answer keys of multiple-choice "
    "questions in skills tests, in any field, on the facts alone."
)

# The key check is told the question's kind: a single-answer question has exactly one correct
# option, a select-all-that-apply one 2 or 3 (prepza_common.multi_answer).
SINGLE_ANSWER_KEY = """This is a single-answer question. Return correct_indexes: a list with the
number of the one option that is correct for the question exactly as written. Return null when
none of the options is correct, or when more than one could be defended as correct."""

MULTI_ANSWER_KEY = """This is a select-all-that-apply question: 2 or 3 of its 4 options are
correct, never all of them. Judge each option on its own. Return correct_indexes: the numbers of
every option that is correct for the question exactly as written. Return null when fewer than two
or all four are correct, or when any option could be defended both as correct and as wrong."""

VERIFY_PROMPT = """Check the multiple-choice interview question below. People who answered it, or
reported it, suggest its answer key may be wrong. Work out the right answer on the facts alone:
the reports only explain why it's being checked, they don't decide what is right, and no option
is marked.

{kind}

Level: {level}
Topic: {topic}

<question>
{question}
</question>

<options>
{options}
</options>

Reports from users (reason: how many):
<reports>
{reports}
</reports>
"""

# A second, blind look before a key moves: no option is marked and they come in a new order, so
# the answer can't lean on the first check's or on a position.
CONFIRM_PROMPT = """Answer the multiple-choice interview question below on the facts alone.

{kind}

Level: {level}
Topic: {topic}

<question>
{question}
</question>

<options>
{options}
</options>
"""

# The self-check of a new select-all-that-apply question, before it's kept: a blind answer, as
# CONFIRM_PROMPT's, and whether the question leaves open a condition that decides an option.
SELF_CHECK_PROMPT = """Answer the select-all-that-apply interview question below on the facts
alone, then check whether it can be answered with certainty.

{kind}

Then return open_condition: a few words naming a condition the question leaves unstated that
decides whether some option is right or wrong, so the option could flip under one reasonable
reading and not another: the standard, law, framework or version in use; which substance,
target, party, role, object or value in the scenario is meant; the order or timing of events;
a region or register of a language; or a case such as two values being equal. Null when every
such condition is stated or no reasonable reading flips an option.

Level: {level}
Topic: {topic}

<question>
{question}
</question>

<options>
{options}
</options>
"""
