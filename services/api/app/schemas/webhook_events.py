from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.public import CandidateEvent, InterviewEvent, RemovedEvent, TestEvent

EXAMPLE_AT = "2026-10-15T08:30:00+00:00"


class WebhookEvent(BaseModel):
    """What every web hook request's body holds, besides the event's `data`."""

    id: str = Field(
        description="The event's id: the same when it's sent again, so ignore one you've had",
        examples=["9f1c2b7e-4d3a-4b8e-9a51-0c6e2f1d7a44"],
    )
    occurred_at: datetime = Field(
        description="When the change happened, to put events in order: a retried one can "
        "arrive after a later one",
        examples=[EXAMPLE_AT],
    )


class CandidateWebhook(WebhookEvent):
    type: Literal[
        "candidate.finished", "candidate.started", "candidate.undelivered", "candidate.expired"
    ] = Field(description="The event's type")
    data: CandidateEvent


class RemovedWebhook(WebhookEvent):
    type: Literal["candidate.removed"] = Field(description="The event's type")
    data: RemovedEvent


class InterviewWebhook(WebhookEvent):
    type: Literal["interview.ready"] = Field(description="The event's type")
    data: InterviewEvent


class TestWebhook(WebhookEvent):
    type: Literal["test"] = Field(description="The event's type")
    data: TestEvent
