from enum import StrEnum

from testee_common.config.constants import (  # noqa: F401 (re-exported)
    MAX_INTERVIEW_QUESTIONS,
    MAX_QUESTION_SECONDS,
    MIN_QUESTION_SECONDS,
)


class InterviewStatus(StrEnum):
    """Where a test stands, as its lists show it (helpers/interviews.py decides)."""

    # No candidate invited yet.
    NEW = "new"
    # Candidates invited.
    IN_PROCESS = "in_process"
    # The company marked it as hired.
    HIRED = "hired"


# A generation's status (as generation reports it) once it has failed and waits for a retry.
GENERATION_FAILED_STATUS = "failed"
# A medium test's seconds a question are a new generated test's until its level is known.
UNKNOWN_LEVEL = "medium"
# The grade, in percent, a finished candidate needs to pass, and the range a company can set.
DEFAULT_PASS_MARK = 70
MIN_PASS_MARK = 1
MAX_PASS_MARK = 100
# The settings whose change the action log records as interview_settings_changed (the pass mark
# has an action of its own).
SETTINGS_LOGGED = {"question_seconds", "hired", "keep_private", "voice"}
# Questions each candidate gets from a topic until a manager sets another number, drawn at random
# from the topic's whole bank: a new interview's topics share MAX_INTERVIEW_QUESTIONS evenly, this
# many each at most (helpers/interviews.py topic_limits).
DEFAULT_TOPIC_QUESTIONS = 10
# A topic's number of questions that would take the interview over MAX_INTERVIEW_QUESTIONS.
TOO_MANY_QUESTIONS = "At most {most} questions per candidate; {left} left."
# Setting the last topic with questions to 0 (a topic at 0 is left out of the interview).
NO_QUESTIONS_LEFT = "An interview needs at least one topic with questions."
# Turning voice mode on for an interview in a language speech isn't reliable in.
VOICE_NOT_IN_LANGUAGE = "Voice mode isn't available in this interview's language."
# A test's topics with their question counts, from library, kept this long by each companies
# instance for the test's page: a count that changes (a question revealed in practice is no
# longer served) shows within it. Candidates starting always read the questions afresh.
SET_CACHE_SECONDS = 30
# A company's previews used up for the day; voice mode's have their own, smaller limit.
PREVIEWS_USED_UP = (
    "Your company has used all of today's click mode previews ({limit}). Try again in {hours} h."
)
VOICE_PREVIEWS_USED_UP = (
    "Your company has used all of today's voice mode previews ({limit}). Try again in {hours} h."
)
