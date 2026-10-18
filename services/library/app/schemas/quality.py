from datetime import datetime

from prepza_common.constants import MAX_PAGE_SIZE
from prepza_common.sets import OptionIn
from pydantic import AwareDatetime, BaseModel, Field


class ReportNote(BaseModel):
    reason: str
    comment: str


class QuestionQuality(BaseModel):
    """What the verifier looks at: the question, how it's answered and what users reported."""

    text: str
    options: list[OptionIn]
    answers: int
    option_picks: dict[str, int]
    reports: list[ReportNote]
    # The flag the verifier acts on; None once the question was kept or replaced since.
    flag: str | None = None


class QuestionUpdatesIn(BaseModel):
    company_ids: list[str] = Field(max_length=MAX_PAGE_SIZE)
    since: AwareDatetime
    until: AwareDatetime


class QuestionUpdateOut(BaseModel):
    """A question of a company's interview newly flagged (question_flagged) or fixed
    (question_fixed), named by its topic as the bell names it."""

    kind: str
    at: datetime
    company_id: str
    title: str
    topic: str
    link: str


class QuestionUpdatesOut(BaseModel):
    items: list[QuestionUpdateOut]
