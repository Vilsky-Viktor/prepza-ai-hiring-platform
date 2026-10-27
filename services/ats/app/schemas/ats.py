from datetime import datetime
from uuid import UUID

from prepza_common.config.constants import MAX_PAGE_SIZE
from pydantic import AwareDatetime, BaseModel, Field

from app.constants.ats import AtsProvider, ConnectionStatus


class ConnectionOut(BaseModel):
    """A connection as the company sees it: never its key."""

    provider: AtsProvider
    account: str
    status: ConnectionStatus
    created_at: datetime


class IntegrationsOut(BaseModel):
    # Whether integrations are set up on this server (an encryption key is set).
    available: bool
    connections: list[ConnectionOut]


class WorkableIn(BaseModel):
    # The account's subdomain or address (acme, acme.workable.com), and its API access token.
    account: str = Field(min_length=1, max_length=200)
    token: str = Field(min_length=1, max_length=500)


class GreenhouseIn(BaseModel):
    # A Harvest V3 (OAuth) API credential's client ID and secret.
    client_id: str = Field(min_length=1, max_length=200)
    client_secret: str = Field(min_length=1, max_length=500)


class BreezyIn(BaseModel):
    # A personal API key from Breezy HR (My Settings > API Keys).
    token: str = Field(min_length=1, max_length=500)


class RecruiteeIn(BaseModel):
    # The company's Recruitee address (acme, acme.recruitee.com) and a personal API token.
    account: str = Field(min_length=1, max_length=200)
    token: str = Field(min_length=1, max_length=500)


class TeamtailorIn(BaseModel):
    # An API key with Admin permission, Read/Write.
    key: str = Field(min_length=1, max_length=500)


class WebhookKeyIn(BaseModel):
    # The signature key the ATS generated for the company's web hook.
    secret: str = Field(min_length=1, max_length=500)


class WebhookOut(BaseModel):
    """What the company pastes into its ATS's web hook: where it sends, and its secret key."""

    url: str
    secret: str


class AtsItemOut(BaseModel):
    """A job or a stage in the ATS: its own id and name."""

    id: str
    name: str


class JobLinkIn(BaseModel):
    provider: AtsProvider
    job_id: str = Field(min_length=1, max_length=100)
    stage_id: str = Field(min_length=1, max_length=100)
    interview_id: UUID


class JobLinkOut(BaseModel):
    id: UUID
    provider: AtsProvider
    job_name: str
    stage_name: str
    interview_id: UUID
    interview_title: str | None
    # Candidates the ATS sent for this job: invited, not invited (to retry), and waiting for
    # the interview to be ready.
    invited: int = 0
    not_invited: int = 0
    waiting: int = 0


class JobTextOut(BaseModel):
    """A job's text to make an interview from, which the company can edit first."""

    text: str


class NotInvitedIn(BaseModel):
    company_ids: list[UUID] = Field(max_length=MAX_PAGE_SIZE)
    since: AwareDatetime
    until: AwareDatetime


class NotInvitedOut(BaseModel):
    """A candidate an ATS sent who couldn't be invited, and why (FailReason); `link` is the
    ATS's page, where they're retried."""

    at: datetime
    company_id: UUID
    interview_id: UUID
    title: str | None
    ats: str
    email: str
    candidate_name: str | None
    reason: str | None
    link: str


class NotInvitedListOut(BaseModel):
    """The newest MAX_UPDATES, and how many there are in all."""

    items: list[NotInvitedOut]
    total: int
