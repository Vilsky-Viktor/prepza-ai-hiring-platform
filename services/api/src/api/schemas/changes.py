from typing import Literal

from prepza_common.auth.user import Language
from prepza_common.config.constants import MAX_GOAL_LENGTH, MAX_NOTE_LENGTH
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from api.constants import examples


class InterviewIn(BaseModel):
    """The job to make an interview for."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"job_description": "Backend developer: Python, Postgres, APIs."}]
        }
    )

    job_description: str = Field(
        min_length=1,
        max_length=MAX_GOAL_LENGTH,
        description=(
            f"The job description to make the interview from, at most {MAX_GOAL_LENGTH} characters"
        ),
    )
    language: Language | None = Field(
        default=None,
        description=(
            "The language to write the interview in, as a code such as `en` or `de`; by "
            "default the job description's own"
        ),
    )


class CandidateUpdate(BaseModel):
    """Only the fields given change, all or none."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"name": "Anna Nowak"}]})

    name: str | None = Field(
        default=None,
        max_length=200,
        description="The candidate's name; an empty string makes it unknown",
    )
    extra_time: Literal[0, 25, 50, 100] | None = Field(
        default=None,
        description=(
            "Extra time on each question, in percent, for a candidate who needs it; only "
            "before they start (409 after)"
        ),
    )


class NoteIn(BaseModel):
    """The note to add."""

    model_config = ConfigDict(json_schema_extra={"examples": [examples.NOTE_IN]})

    text: str = Field(
        min_length=1,
        max_length=MAX_NOTE_LENGTH,
        description=(
            f"The note, as plain text, at most {MAX_NOTE_LENGTH} characters; line breaks are "
            "kept, and blanks at either end are dropped"
        ),
    )


class CandidateSearch(BaseModel):
    email: EmailStr = Field(
        description="The email the candidate was invited with", examples=["anna@example.com"]
    )


class Credits(BaseModel):
    """Your company's credits."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"available": 4500, "reserved": 1000, "candidates": 9, "low": False}]
        }
    )

    available: int = Field(description="Credits your company can spend now")
    reserved: int = Field(description="Credits set aside for candidates who haven't finished")
    candidates: int = Field(description="How many more candidates the available credits pay for")
    low: bool = Field(description="Whether the credits are running low")
