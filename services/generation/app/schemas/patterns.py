from datetime import datetime
from uuid import UUID

from prepza_common.sets import OptionIn
from pydantic import BaseModel, Field


class QualitySignal(BaseModel):
    """A question flagged or replaced lately, as library's /internal/questions/signals gives it:
    no id, set or company."""

    flag: str
    text: str
    options: list[OptionIn]
    answers: int
    correct: float
    option_picks: dict[str, int]
    timeouts: int
    reasons: dict[str, int]
    likes: int
    dislikes: int
    new_text: str | None = None
    new_options: list[OptionIn] | None = None


class ProposedPattern(BaseModel):
    text: str = Field(description="The mistake as one short general rule, in English.")
    questions: list[int] = Field(description="The numbers of the questions that show it.")
    same_as: int | None = Field(
        description="The number of the known pattern that describes the same mistake, or null "
        "when it is new."
    )


class ProposedPatterns(BaseModel):
    patterns: list[ProposedPattern]


class PatternOut(BaseModel):
    """A pattern on the admin zone's patterns tab."""

    id: UUID
    text: str
    flag: str
    question_count: int
    first_seen: datetime
    last_seen: datetime
    status: str
    reviewed_at: datetime | None
