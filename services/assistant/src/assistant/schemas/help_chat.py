from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from assistant.constants.chat import QUESTION_TOO_LONG
from assistant.constants.help_chat import (
    LAST_NOT_QUESTION,
    MAX_HELP_MESSAGE_LENGTH,
    MAX_HELP_MESSAGES,
    MAX_HELP_QUESTION_LENGTH,
    MAX_PAGE_KEY_LENGTH,
    SIGNATURE_LENGTH,
    TRACE_ID_LENGTH,
    HelpRole,
)


class HelpMessage(BaseModel):
    role: HelpRole
    content: str = Field(min_length=1, max_length=MAX_HELP_MESSAGE_LENGTH)
    # A reply's signature, as the help chat gave it when it wrote the reply.
    signature: str | None = Field(default=None, max_length=SIGNATURE_LENGTH)


class HelpChatRequest(BaseModel):
    """The conversation so far, ending with the new question; the page keeps it. `page`: the
    key of the page the visitor asks on, whose guide the answer reads (an unknown one is
    ignored)."""

    messages: list[HelpMessage] = Field(min_length=1, max_length=MAX_HELP_MESSAGES)
    page: str | None = Field(default=None, max_length=MAX_PAGE_KEY_LENGTH)
    # The conversation's own id, made by the page: its answers' traces share a session.
    chat_id: UUID | None = None

    @model_validator(mode="after")
    def ends_with_question(self):
        question = self.messages[-1]

        if question.role != HelpRole.USER:
            raise ValueError(LAST_NOT_QUESTION)

        if len(question.content) > MAX_HELP_QUESTION_LENGTH:
            raise ValueError(QUESTION_TOO_LONG)

        return self


class HelpVoteIn(BaseModel):
    """A thumbs up (1) or down (-1) on a help chat answer, null to clear it, with the answer's
    run and signature as its last event gave them."""

    trace_id: str | None = Field(default=None, max_length=TRACE_ID_LENGTH)
    signature: str = Field(max_length=SIGNATURE_LENGTH)
    value: Literal[1, -1] | None


class HelpKnowledge(BaseModel):
    """What rounds sends the help chat to answer from, in English: the platform guide (with the
    prices in the visitor's currency) and the guide of the page asked on, if it's a known one."""

    knowledge: str
    page_guide: str | None = None
