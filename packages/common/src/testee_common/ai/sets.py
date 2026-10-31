from uuid import UUID

from pydantic import BaseModel
from testee_common.config.constants import DEFAULT_LANGUAGE


class OptionIn(BaseModel):
    answer: str
    correct: bool


class QuestionIn(BaseModel):
    text: str
    options: list[OptionIn]
    # A question taken from the bank: its original, whose statistics its answers add to.
    source_id: UUID | None = None


class TopicIn(BaseModel):
    title: str
    subtopics: list[str]
    questions: list[QuestionIn]
    # Lets the question bank find this topic by meaning (library's repositories/reuse.py).
    embedding: list[float] | None = None


class PreparationIn(BaseModel):
    """A generated test, as generation saves it in library."""

    # Lets library return the same set when a save is retried.
    generation_id: UUID
    owner_uid: str
    source_text: str
    title: str
    level: str
    requirements: list[str]
    topics: list[TopicIn]
    language: str = DEFAULT_LANGUAGE


class AdditionTopic(BaseModel):
    """A template topic, as generation needs it to add questions to it."""

    id: UUID
    title: str
    subtopics: list[str]
    # Every question's text, so new ones repeat none.
    texts: list[str]
    # What it lacks of the practice and company questions a template topic is meant to hold.
    practice_missing: int
    company_missing: int


class AdditionContext(BaseModel):
    """A template's topics, for adding questions to them (library's internal_additions.py)."""

    level: str
    language: str
    topics: list[AdditionTopic]


class TopicAdditionIn(BaseModel):
    """New questions for one topic of a template, by the pool each goes to."""

    topic_id: UUID
    practice: list[QuestionIn]
    company: list[QuestionIn]


class AddedQuestionsIn(BaseModel):
    """Questions generation adds to a template's topics, saved in one go."""

    topics: list[TopicAdditionIn]
