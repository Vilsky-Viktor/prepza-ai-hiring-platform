from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from rounds.schemas.review import ReviewItem


class PracticeStartIn(BaseModel):
    """How a new practice round is timed: one of PRACTICE_TIMINGS (constants/practice.py)."""

    timing: Literal["standard", "double", "untimed"] = Field(
        "standard", description="The time per question: standard, double, or no time limit."
    )


class PracticeStartOut(BaseModel):
    """A new practice round: its id, and the first section to open."""

    round_id: UUID
    session_id: UUID


class PracticeTopicResult(BaseModel):
    # The section, for rating and reporting its questions.
    session_id: UUID
    title: str
    # None until the section is finished.
    score: int | None
    review: list[ReviewItem]


class PracticeRoundOut(BaseModel):
    """A talent's round, with every question's right answer once it's finished."""

    round_id: UUID
    template_id: UUID
    title: str | None
    # The language the questions are written in, which can differ from the page's.
    language: str | None = None
    finished: bool
    # The share of the round's questions answered right; None until it's finished.
    grade: int | None
    # Questions the talent picked an answer for (not timed out), and all the round's questions.
    answered: int
    total: int
    started_at: datetime
    # The first section still open, to continue an unfinished round.
    open_session_id: UUID | None
    topics: list[PracticeTopicResult]


class PracticeRoundSummary(BaseModel):
    round_id: UUID
    started_at: datetime
    finished: bool
    # The share of the round's questions answered, in percent.
    progress: int
    grade: int | None


class PracticeTopicProgress(BaseModel):
    """How far the talent got on one of the template's topics in their latest round."""

    topic_id: UUID
    answered: int
    total: int


class PracticeStatusOut(BaseModel):
    """Where the talent is on a template they practiced, from their latest round on it; a
    template missing from the list was never started."""

    template_id: UUID
    status: Literal["in_progress", "completed"]
    # The latest round's finished topics, and all its topics.
    topics_done: int
    topics_total: int


class PracticeTimingOut(BaseModel):
    """A time per question the talent can choose before a round."""

    id: str
    # The seconds each question has; None for no time limit.
    seconds: int | None


class PracticeSizeOut(BaseModel):
    """How many questions a practice round on the template has, and the times per question to
    choose from, standard first."""

    questions: int
    # How many of them each topic gets, by the topic's id: its progress reads 0/N before it's
    # started.
    topics: dict[str, int]
    timings: list[PracticeTimingOut]
