# The weekly pattern job (services/patterns.py): the recurring mistakes in questions of one flag,
# as general rules. Task wording only, and nothing tied to a subject: the rules must hold for
# questions on anything.

# What the questions of each flag (library's QualityFlag) have in common.
FLAG_MEANINGS = {
    "wrong_key": "the option marked correct looked wrong to the people who answered or reported "
    "them.",
    "rewrite": "they were unclear, hard to read, off the subject, disliked, far too hard, too "
    "slow to read, or did not tell strong candidates from weak ones.",
    "weak_options": "almost everybody got them right, or a wrong option was almost never picked.",
}

PATTERNS_PROMPT = """Below are multiple-choice questions from many different tests. All of them
were found to be bad: {meaning}

Each question comes with its options (correct ones marked, with the share of answers that picked
each), how often it was answered right, what users reported, and, when it was replaced, the
question that replaced it.

Find the mistakes in how these questions are written that recur in at least {min_questions} of
them. Describe each as a short general rule that helps anyone write better questions on any
subject, for example:
- The scenario leaves out the detail that decides the answer.
- One wrong option is the only negative statement, so it is ruled out at once.
- Two options say the same thing in different words.

Each rule:
- is one sentence in English, at most {max_chars} characters;
- describes how a question is written, never what it is about: it names no organisation,
  product, tool, standard, profession, subject area, place or person, and uses no term of any
  particular subject;
- never quotes the questions or their options;
- lists the numbers of the questions that show it.

Known patterns:
{known}

When a mistake is one of the known patterns, return that pattern's number as same_as instead of
writing it again in other words. Return no rule when no mistake recurs.

Questions:
{questions}
"""
