from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from generation.constants.generation import MAX_STATUSES_PER_CALL
from generation.constants.statuses import Status


class GenerationIdsIn(BaseModel):
    ids: list[UUID] = Field(max_length=MAX_STATUSES_PER_CALL)


class GenerationStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: Status
    # Who started it.
    owner_uid: str
    # When its status last changed: for one awaiting review, since when it waits.
    updated_at: datetime


class GenerationStatusesOut(BaseModel):
    generations: list[GenerationStatusOut]
