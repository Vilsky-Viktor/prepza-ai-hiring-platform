"""An interview's generation as the generation service returns it."""

from uuid import UUID

from pydantic import BaseModel


class DraftTopic(BaseModel):
    main_topic: str
    subtopics: list[str]


class GenerationProgress(BaseModel):
    done: int
    total: int
    # Missing on generations started before per-topic progress existed.
    topics: int | None = None
    topics_ready: int | None = None


class GenerationOut(BaseModel):
    id: UUID
    kind: str
    company_id: UUID | None
    # queued, running, awaiting_review, done, failed or cancelled.
    status: str
    # The drafted topics, for the review.
    topics: list[DraftTopic] | None
    progress: GenerationProgress | None
    preparation_id: UUID | None
    error: str | None
    # What it's generated in.
    language: str
    # How many topics the review may approve without instructions, and subtopics a topic may
    # have when edited by hand.
    max_topics: int
    max_subtopics: int
