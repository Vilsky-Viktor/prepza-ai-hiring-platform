from datetime import datetime
from uuid import UUID

from prepza_common.sets import OptionIn
from pydantic import BaseModel


class FlaggedQuestionOut(BaseModel):
    """A question flagged now, for the admin zone's quality tab."""

    question_id: UUID
    text: str
    options: list[OptionIn]
    flag: str
    # A template's questions can be fixed now or dismissed here; a company's only viewed.
    actionable: bool
    answers: int
    correct: float
    reports: int
    set_title: str
    # A template, or a company's test.
    set_kind: str
    # When it was flagged.
    at: datetime


class ReplacedQuestionOut(BaseModel):
    """A question's old content, kept when it was replaced."""

    # The kept revision, whose reports can be listed.
    revision_id: UUID
    question_id: UUID
    # Its old text and options, as they were before it was replaced.
    text: str
    options: list[OptionIn]
    answers: int
    correct: float
    reports: int
    set_title: str
    set_kind: str
    # When it was replaced.
    at: datetime
    # What replaced it: the question's next version.
    new_text: str
    new_options: list[OptionIn]


class QualitySignalOut(BaseModel):
    """A question flagged or replaced lately, for generation's weekly pattern job: its content
    and what showed it was bad, without any id, set or company."""

    flag: str
    text: str
    options: list[OptionIn]
    answers: int
    correct: float
    # Times each option was picked, keyed by its text.
    option_picks: dict[str, int]
    timeouts: int
    # Reports per reason; never their comments.
    reasons: dict[str, int]
    likes: int
    dislikes: int
    # What replaced it, for a replaced question.
    new_text: str | None = None
    new_options: list[OptionIn] | None = None
