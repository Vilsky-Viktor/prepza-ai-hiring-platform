from datetime import datetime
from uuid import UUID

from prepza_common.constants import MAX_PAGE_SIZE
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class NotificationOut(BaseModel):
    """What the bell shows: `kind` picks the text, `data` fills it, `link` opens the page."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kind: str
    link: str
    data: dict
    created_at: datetime


class FeedOut(BaseModel):
    items: list[NotificationOut]
    # Newer than the user's last look at the bell.
    unread: int


class UpdatesIn(BaseModel):
    """The companies whose notifications to read, after `since` and up to `until`."""

    company_ids: list[UUID] = Field(max_length=MAX_PAGE_SIZE)
    since: AwareDatetime
    until: AwareDatetime


class UpdateOut(NotificationOut):
    company_id: str = Field(validation_alias="recipient_id")


class UpdatesOut(BaseModel):
    items: list[UpdateOut]
