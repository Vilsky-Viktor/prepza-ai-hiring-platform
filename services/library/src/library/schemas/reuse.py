from uuid import UUID

from prepza_common.ai.sets import OptionIn
from prepza_common.config.constants import DEFAULT_LANGUAGE
from pydantic import BaseModel, Field

from library.constants.reuse import MAX_REUSE_COUNT


class ReuseIn(BaseModel):
    embedding: list[float]
    level: str
    language: str = DEFAULT_LANGUAGE
    count: int = Field(ge=1, le=MAX_REUSE_COUNT)
    # A company interview's company: the shared bank's questions are offered too, never the
    # company's own. None for a template, which reuses only templates' questions.
    company_id: UUID | None = None


class TopicToEmbed(BaseModel):
    id: UUID
    title: str
    subtopics: list[str]


class TopicEmbedding(BaseModel):
    id: UUID
    embedding: list[float]


class ReusedQuestion(BaseModel):
    # The question it's taken from: a template's, or a shared bank question.
    source_id: UUID
    text: str
    options: list[OptionIn]
