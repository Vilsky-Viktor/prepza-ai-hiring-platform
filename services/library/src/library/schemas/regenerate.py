from uuid import UUID

from pydantic import BaseModel, Field
from testee_common.ai.sets import OptionIn


class QuestionContext(BaseModel):
    """What the generator needs to replace a question without repeating its topic."""

    set_id: UUID
    kind: str
    owner_id: str
    level: str
    language: str
    topic: str
    subtopics: list[str]
    existing: list[str]
    # A multi-answer ("select all that apply") question: its replacement is one too.
    multi: bool = False
    # A question with an example (testee_common.ai.examples): its replacement has one too.
    example: bool = False


class QuestionReplace(BaseModel):
    text: str = Field(min_length=1)
    options: list[OptionIn]
