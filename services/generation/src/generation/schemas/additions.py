from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field, field_validator

from generation.constants.additions import (
    ADDED_QUESTIONS_INVALID,
    ADDED_QUESTIONS_STEP,
    DEFAULT_ADDED_QUESTIONS,
    MAX_ADDED_QUESTIONS,
)
from generation.constants.statuses import Status
from generation.schemas.generation import GenerationProgress


class AdditionCreate(BaseModel):
    """A superadmin's addition: the questions to add to every topic of a template."""

    count: int = DEFAULT_ADDED_QUESTIONS

    @field_validator("count")
    @classmethod
    def in_steps_up_to_the_most(cls, count: int) -> int:
        if not ADDED_QUESTIONS_STEP <= count <= MAX_ADDED_QUESTIONS or count % ADDED_QUESTIONS_STEP:
            raise ValueError(ADDED_QUESTIONS_INVALID)

        return count


class AdditionOut(BaseModel):
    """A template's latest question addition, none when it never had one, and the numbers a
    superadmin's addition may ask for."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    status: Status | None = None
    progress: GenerationProgress | None = None
    error: str | None = None

    @computed_field
    @property
    def default_count(self) -> int:
        return DEFAULT_ADDED_QUESTIONS

    @computed_field
    @property
    def count_step(self) -> int:
        return ADDED_QUESTIONS_STEP

    @computed_field
    @property
    def max_count(self) -> int:
        return MAX_ADDED_QUESTIONS
