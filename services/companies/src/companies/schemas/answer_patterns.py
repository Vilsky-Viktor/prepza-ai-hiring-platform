"""What a candidate's answers and times show, from rounds (its helpers/integrity_report.py)."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class PatternSignal(BaseModel):
    """A signal that fired: `timing`, answer times that didn't follow the questions' length and
    difficulty; `person_fit`, right and wrong answers that didn't follow difficulty, with its
    counts (of the harder half of the questions, how many right; of the easier half, how many
    wrong)."""

    kind: Literal["timing", "person_fit"]
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
    right: list[str]
    wrong: str


class AnswerPatterns(BaseModel):
    """The signals that fired (empty when none did) and questions to ask in a live interview;
    both empty until the candidate finishes."""

    signals: list[PatternSignal] = []
    follow_ups: list[FollowUp] = []
