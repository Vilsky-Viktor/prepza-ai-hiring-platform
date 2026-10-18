from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID | None
    title: str
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    """A message as the panel shows it: never the tools' raw results."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    source: str
    content: str
    blocks: list[dict]
    status: str
    # The user's thumbs up (1) or down (-1) on an answer.
    vote: int | None
    created_at: datetime


class ConversationDetailOut(ConversationOut):
    messages: list[MessageOut]


class VoteIn(BaseModel):
    """A thumbs up (1) or down (-1) on an answer; null clears it."""

    value: Literal[1, -1] | None
