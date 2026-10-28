from uuid import UUID

from prepza_common.ai.page_keys import PAGE_KEYS
from pydantic import BaseModel, Field, field_validator

from assistant.constants.chat import (
    HISTORY_MESSAGES,
    MAX_MESSAGE_LENGTH,
    MAX_PAGE_LENGTH,
    PAGE_ID_PATTERN,
    QUESTION_TOO_LONG,
    Role,
    Source,
)
from assistant.constants.welcome import Stage


class EarlierTurn(BaseModel):
    """A message from before the user signed in (the panel's visitor chat), cut to the length a
    message may have."""

    role: Role
    content: str = Field(min_length=1)

    @field_validator("content")
    @classmethod
    def cut(cls, content: str) -> str:
        return content[:MAX_MESSAGE_LENGTH]


class PageContext(BaseModel):
    """The page the user is on, only as context for the model: its guide's key (an unknown one
    is dropped), its path with the query (the tab), cut to MAX_PAGE_LENGTH, and the ids it's
    about. The ids are never trusted: the tools read with the user's token, so one that isn't
    theirs is a 404 there."""

    key: str | None = None
    path: str
    company_id: str | None = Field(default=None, pattern=PAGE_ID_PATTERN)
    interview_id: str | None = Field(default=None, pattern=PAGE_ID_PATTERN)
    candidate_id: str | None = Field(default=None, pattern=PAGE_ID_PATTERN)
    template_id: str | None = Field(default=None, pattern=PAGE_ID_PATTERN)
    practice_round_id: str | None = Field(default=None, pattern=PAGE_ID_PATTERN)

    @field_validator("key")
    @classmethod
    def known(cls, key: str | None) -> str | None:
        return key if key in PAGE_KEYS else None

    @field_validator("path")
    @classmethod
    def cut(cls, path: str) -> str:
        return path[:MAX_PAGE_LENGTH]


class ChatRequest(BaseModel):
    """A new message: in a conversation, or starting one. `company_id`: the company picked in
    the panel (none: all companies), which this message is about; a new conversation is listed
    under it. `page`: the page the user asks on, only as context. `earlier`: the chat the user
    had before signing in, saved first into a new conversation (ignored in an existing one)."""

    conversation_id: UUID | None = None
    company_id: UUID | None = None
    message: str = Field(min_length=1)
    source: Source = Source.TEXT
    page: PageContext | None = None
    earlier: list[EarlierTurn] = Field(default_factory=list, max_length=HISTORY_MESSAGES)

    @field_validator("message")
    @classmethod
    def short_enough(cls, message: str) -> str:
        if len(message) > MAX_MESSAGE_LENGTH:
            raise ValueError(QUESTION_TOO_LONG)

        return message


class ConfigOut(BaseModel):
    """The limits the panel shows and keeps to."""

    max_message_length: int
    # A chat older than this isn't brought back after a reload.
    restore_minutes: int
    max_audio_seconds: int
    messages_per_hour: int
    messages_per_day: int


class WelcomeOut(BaseModel):
    stage: Stage
