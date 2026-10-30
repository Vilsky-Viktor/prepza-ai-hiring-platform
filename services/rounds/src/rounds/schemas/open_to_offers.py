from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from rounds.constants.open_to_offers import MAX_MATCH_TOPICS


class OpenToOffersIn(BaseModel):
    """Turning Open to offers on, or changing the profile: the LinkedIn profile's address and the
    version of the switch's wording the person saw (`consent_version` of OpenToOffersOut)."""

    linkedin_url: str = Field(max_length=300)
    consent_version: str = Field(max_length=16)


class OpenToOffersOut(BaseModel):
    on: bool
    # The name and profile shared while it's on.
    name: str | None = None
    linkedin_url: str | None = None
    # When it lapses unless turned on again (OPEN_DAYS after it was last turned on).
    until: datetime | None = None
    # The switch's current wording, which turning it on agrees to.
    consent_version: str


class MatchesIn(BaseModel):
    """Companies, for an interview's Discover tab: the template topics it matches."""

    topic_ids: list[UUID] = Field(max_length=MAX_MATCH_TOPICS)
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class PracticeResultOut(BaseModel):
    """A practice topic's latest timed result: practice, never a company's interview."""

    topic_title: str
    # The grade, in percent.
    score: int
    finished_at: datetime


class MatchOut(BaseModel):
    user_id: str
    name: str | None
    linkedin_url: str
    results: list[PracticeResultOut]


class OpenProfileOut(BaseModel):
    user_id: str
    name: str | None
    linkedin_url: str
