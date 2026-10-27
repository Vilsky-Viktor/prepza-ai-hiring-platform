from uuid import UUID

from prepza_common.ai.sets import OptionIn
from prepza_common.config.constants import DEFAULT_LANGUAGE
from pydantic import BaseModel, Field

from app.constants.reuse import MAX_REUSE_COUNT


class ReuseIn(BaseModel):
    embedding: list[float]
    level: str
    language: str = DEFAULT_LANGUAGE
    count: int = Field(ge=1, le=MAX_REUSE_COUNT)


class TopicToEmbed(BaseModel):
    id: UUID
    title: str
    subtopics: list[str]


class TopicEmbedding(BaseModel):
    id: UUID
    embedding: list[float]


class ReusedQuestion(BaseModel):
    # The bank question it's taken from.
    source_id: UUID
    text: str
    options: list[OptionIn]
