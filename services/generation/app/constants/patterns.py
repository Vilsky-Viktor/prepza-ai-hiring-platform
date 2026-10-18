from enum import StrEnum


class PatternStatus(StrEnum):
    """Where a quality pattern stands: proposed by the weekly job, then approved or dismissed
    by a superadmin; an approved one in use once an eval shows it helps."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    DISMISSED = "dismissed"
    IN_USE = "in_use"


# The weekly job reads the questions flagged or replaced in this many days.
PATTERN_WINDOW_DAYS = 7
# Questions of one flag the model reads in a run, newest first; the rest wait for next week.
MAX_PATTERN_QUESTIONS = 60
# A mistake shown by fewer questions than this isn't recurring.
MIN_PATTERN_QUESTIONS = 2
# Longest pattern kept, in characters: a short general rule.
MAX_PATTERN_CHARS = 300
# A pattern sharing this many words in a row with an input question quotes it.
QUOTED_WORDS = 6
# One pattern run at a time; the lock outlasts the worker's 30-minute request timeout.
PATTERN_LOCK_KEY = "lock:quality-patterns"
PATTERN_LOCK_SECONDS = 30 * 60
# A flag's questions are read once a week: a retried or repeated run in the same week skips the
# flags already done, so no question is counted twice.
PATTERN_DONE_KEY = "done:quality-patterns:{flag}"
PATTERN_DONE_SECONDS = 6 * 24 * 60 * 60
# Words that name a technology, a standard, a field or a role: a pattern must hold for any
# domain, so one with these is rejected (the prompt test keeps generation's prompts clear of
# them the same way). Capitalized words inside a pattern (names of companies, products,
# technologies) are rejected too (helpers/patterns.py).
DENIED_TERMS = (
    "debug",
    "software",
    "engineer",
    "developer",
    "code",
    "technical",
    "technology",
    "program",
    "sql",
    "query",
    "shell",
    "spreadsheet",
    "regular expression",
    "regex",
    "python",
    "javascript",
    "typescript",
    "rust",
    "decorator",
    "transaction",
    "database",
    "ifrs",
    "gaap",
    "crm",
    "salesforce",
    "hubspot",
    "seo",
    "marketing",
    "accounting",
    "nursing",
    "keyword",
    "company",
    "employer",
    "role",
    "job",
)
