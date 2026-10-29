from uuid import UUID

from pydantic import BaseModel, Field


class Option(BaseModel):
    answer: str
    correct: bool


class Question(BaseModel):
    id: UUID
    text: str
    options: list[Option]
    # The share of candidates who answer it right, from library when it has enough answers:
    # kept with the session's questions for the integrity signals (helpers/answer_patterns.py).
    difficulty: float | None = Field(default=None, ge=0, le=1)


class TopicQuestions(BaseModel):
    id: UUID
    preparation_id: UUID
    title: str
    questions: list[Question]
