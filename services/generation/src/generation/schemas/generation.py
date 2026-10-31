from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
)
from testee_common.auth.user import Language
from testee_common.config.constants import DEFAULT_LANGUAGE

from generation.constants.generation import (
    MAX_GOAL_LENGTH,
    MAX_INSTRUCTIONS_LENGTH,
    MAX_TOPIC_NAME_LENGTH,
)
from generation.constants.kinds import GenerationKind
from generation.constants.statuses import Status


class InterviewGenerationCreate(BaseModel):
    """From companies, once it has checked the user belongs to the company."""

    text: str = Field(min_length=1, max_length=MAX_GOAL_LENGTH)
    company_id: UUID
    owner_uid: str
    # The recruiter's interface language: the interview is written in the job description's
    # own language, and this only when that can't be told.
    language: Language = DEFAULT_LANGUAGE
    # The language the recruiter chose to generate in; none means the text's own.
    generate_in: Language | None = None
    # Whether the company ever topped up: then it isn't held to the daily limit for everyone.
    paid: bool = False


class TemplateGenerationCreate(BaseModel):
    """An admin's template, from a role description."""

    text: str = Field(min_length=1, max_length=MAX_GOAL_LENGTH)
    # The language to generate in; none means the text's own.
    generate_in: Language | None = None


TopicName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_TOPIC_NAME_LENGTH)
]


class EditedTopic(BaseModel):
    main_topic: TopicName
    # At most MAX_SUBTOPICS, checked with its current value (services/review.py).
    subtopics: list[TopicName]


class ReviewRequest(BaseModel):
    selected: list[int] = Field(min_length=1)
    instructions: str = Field(default="", max_length=MAX_INSTRUCTIONS_LENGTH)
    # Every drafted topic, in order, with the reviewer's own edits; `selected` indexes this list.
    topics: list[EditedTopic] | None = None


class DraftTopic(BaseModel):
    main_topic: str
    subtopics: list[str]


class GenerationProgress(BaseModel):
    """What the progress screen shows; the worker's own per-topic counters stay internal."""

    done: int
    total: int
    # Missing on generations started before per-topic progress existed.
    topics: int | None = None
    topics_ready: int | None = None


class GenerationOut(BaseModel):
    # Its API description lists max_topics and max_subtopics as always there: they always are.
    model_config = ConfigDict(
        from_attributes=True, json_schema_serialization_defaults_required=True
    )

    id: UUID
    kind: GenerationKind
    company_id: UUID | None
    status: Status
    topics: list[DraftTopic] | None
    progress: GenerationProgress | None
    preparation_id: UUID | None
    error: str | None
    # What it's generated in, from the pasted text (testee_common.i18n.text_language).
    language: str

    # How many topics the review may approve without instructions, and how many subtopics a
    # topic may have when edited by hand during review: Controls' current values
    # (services/topic_caps.py).
    max_topics: int = 0
    max_subtopics: int = 0
