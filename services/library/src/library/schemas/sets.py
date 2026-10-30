from uuid import UUID

from pydantic import BaseModel

from library.schemas.preparations import QuestionOut, TopicOut


class SetOut(BaseModel):
    id: UUID
    kind: str
    owner_id: str
    title: str
    level: str
    language: str
    topics: list[TopicOut]


class ContentQuestion(QuestionOut):
    # The share of candidates who answer it right, for rounds' integrity signals; None before
    # it has MIN_ANSWERS answers.
    difficulty: float | None = None


class SetTopicOut(BaseModel):
    id: UUID
    title: str
    questions: list[ContentQuestion]


class SetContent(BaseModel):
    """Internal: every question of an interview, with answers."""

    id: UUID
    title: str
    # basic, medium or hard: a practice round's seconds a question come from it.
    level: str
    topics: list[SetTopicOut]


class PracticeTopicsOut(BaseModel):
    """The template topics a company's interview matches, for its Discover tab."""

    topic_ids: list[UUID]
