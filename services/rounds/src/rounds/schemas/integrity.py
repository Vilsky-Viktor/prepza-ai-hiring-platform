from uuid import UUID

from pydantic import BaseModel

from rounds.constants.answer_patterns import PatternSignal


class PatternSignalOut(BaseModel):
    """A signal that fired, with the numbers its sentence shows."""

    kind: PatternSignal
    # Person-fit: of the harder half of the questions of known difficulty, how many right; of
    # the easier half, how many wrong.
    hard: int | None = None
    hard_right: int | None = None
    easy: int | None = None
    easy_wrong: int | None = None


class FollowUp(BaseModel):
    """A question the candidate answered right, to ask about in a live interview: why the right
    option is right and another isn't."""

    question_id: UUID
    topic_title: str
    text: str
    # The right options, and a wrong one to compare them with.
    right: list[str]
    wrong: str


class AnswerPatternsOut(BaseModel):
    """What the candidate's answers and times show once they've finished: the signals that
    fired (empty when none did), and questions to ask about in a live interview. Both empty
    before they finish."""

    signals: list[PatternSignalOut] = []
    follow_ups: list[FollowUp] = []
