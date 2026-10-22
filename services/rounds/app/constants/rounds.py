from enum import StrEnum


class RoundStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


OPTIONS_PER_QUESTION = 4
# Score of one answer: every question is multiple choice, so it's right or wrong.
CORRECT_SCORE = 100

# The help chat couldn't answer; its replies are short, so a call silent for longer has hung.
CHAT_FAILED = "Couldn't get a reply right now. Please try again."
CHAT_TIMEOUT_SECONDS = 25
# Tries after a failed call. Every try together stays within rounds' request timeout (60 s,
# infra/terraform/locals.tf): beyond it Cloud Run has already cut the answer off, and the calls
# only go on spending.
CHAT_RETRIES = 1

# A timed interview's question ran out of time; it counts as wrong.
TIME_UP = "Time is up for this question."
# A section's review opens once it is finished, so no question is seen before its clock starts.
# Extra seconds an answer may arrive after the deadline, for the trip to the server: a pick still
# on screen is sent when the candidate's clock reaches zero.
TIME_GRACE_SECONDS = 5
# A candidate's whole interview expires at its start plus every question's time and this share
# more; then it finishes by itself, as if the candidate had finished it.
INTERVIEW_TIME_MARGIN = 0.1
# Expired interviews finished per scheduled run; the next run takes the rest.
EXPIRY_BATCH = 100
# A deleted interview's sessions go this many at a time, each batch with its answers and
# signals (cascading) in its own transaction.
SESSION_DELETE_BATCH = 100
# How long an interview's title and language are kept in memory for its candidates' steps.
SET_CACHE_SECONDS = 60
