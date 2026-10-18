from enum import StrEnum


class QualityFlag(StrEnum):
    # The option marked correct looks wrong.
    WRONG_KEY = "wrong_key"
    # Unclear, off topic, disliked, or answered right far less often than by chance.
    REWRITE = "rewrite"
    # A wrong option almost nobody picks, or a question almost everybody gets right.
    WEAK_OPTIONS = "weak_options"


# Answer statistics say nothing before this many answers.
MIN_ANSWERS = 30
TOO_HARD_RATE = 0.15
TOO_EASY_RATE = 0.95
# A wrong option picked by a smaller share of answers adds nothing.
DEAD_OPTION_SHARE = 0.02
# Reports of one reason that flag a question.
REPORTS_TO_FLAG = 2
# Thumbs down that flag a question, when they're also at least twice its thumbs up.
DISLIKES_TO_FLAG = 3
# A candidate whose topic score is at least STRONG_SCORE counts as strong there, one at most
# WEAK_SCORE as weak. A question needs MIN_GROUP_ANSWERS from each before it's judged, and
# separates them when strong candidates get it right at least MIN_SEPARATION more often.
STRONG_SCORE = 70
WEAK_SCORE = 40
MIN_GROUP_ANSWERS = 10
MIN_SEPARATION = 0.1
# Too slow to read: time ran out on at least this share of the times it was shown.
TOO_SLOW_SHARE = 0.25
# A flag the verifier hasn't acted on this long is sent to it again (a lost job, a refusal past
# generation's daily cap); key checks wait for an OpenAI batch, which takes up to a day.
FLAG_RESEND_AFTER_HOURS = 48
# Flags sent again by one daily sweep, oldest first.
MAX_FLAG_RESENDS = 100
# The questions flagged or replaced lately that generation's weekly pattern job reads, newest
# first, at most this many.
MAX_PATTERN_SIGNALS = 500
# Only generation reads them.
PATTERN_SIGNALS_CALLER = "generation"

# The page a company's question notifications open: its interviews (the library doesn't know
# which interview a set belongs to).
COMPANY_INTERVIEWS_LINK = "/companies/{company_id}/interviews"
