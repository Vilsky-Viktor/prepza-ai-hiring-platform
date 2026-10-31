from uuid import UUID

from pydantic import BaseModel
from testee_common.config.constants import DEFAULT_LANGUAGE


class QuestionContext(BaseModel):
    set_id: UUID
    # The set's kind in library: an interview or a template.
    kind: str
    owner_id: str
    level: str
    language: str = DEFAULT_LANGUAGE
    topic: str
    subtopics: list[str]
    existing: list[str]
    # The question is multi-answer ("select all that apply"): its replacement is too.
    multi: bool = False
    # The question shows an example (testee_common.ai.examples): its replacement does too.
    example: bool = False


class RegenerateIn(BaseModel):
    user_id: str
    set_id: UUID
    # Whether the company ever topped up: then it isn't held to the daily limit for everyone.
    paid: bool = False


class RegeneratedOption(BaseModel):
    answer: str
    correct: bool


class RegeneratedQuestion(BaseModel):
    text: str
    options: list[RegeneratedOption]


class RegeneratedOut(BaseModel):
    id: UUID
    text: str
