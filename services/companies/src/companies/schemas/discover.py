from datetime import datetime

from pydantic import BaseModel


class PracticeResultOut(BaseModel):
    """One practice topic's latest timed result: practice, never a company's interview."""

    topic_title: str
    # The grade, in percent.
    score: int
    finished_at: datetime


class DiscoverPersonOut(BaseModel):
    """What a person open to offers shares with a paying company: their name, LinkedIn profile
    and practice results on the interview's subjects. Listed whoever practised last first, never
    ranked."""

    # What the invite names them by.
    id: str
    name: str | None
    linkedin_url: str
    results: list[PracticeResultOut]
