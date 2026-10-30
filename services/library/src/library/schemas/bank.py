from uuid import UUID

from pydantic import BaseModel


class BankCandidate(BaseModel):
    """A company's question offered to the bank's filter, with its topic's title."""

    question_id: UUID
    topic: str
    text: str
    options: list[str]


class BankCheckIn(BaseModel):
    """The filter's verdict on the question's wording `text`."""

    question_id: UUID
    text: str
    passed: bool
