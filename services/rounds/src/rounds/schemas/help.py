from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from rounds.constants.help import (
    LAST_NOT_QUESTION,
    MAX_HELP_MESSAGE_LENGTH,
    MAX_HELP_MESSAGES,
    MAX_HELP_QUESTION_LENGTH,
    MAX_PAGE_KEY_LENGTH,
    QUESTION_TOO_LONG,
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


class FaqItemOut(BaseModel):
    key: str
    question: str
    answer: str


class LegalSectionOut(BaseModel):
    heading: str
    paragraphs: list[str] = []
    items: list[str] = []


class LegalOut(BaseModel):
    # The language of the text: the one asked for when it's translated, otherwise English.
    language: str
    intro: str
    # The day this text applies from, the newest version's, the one that applies today, and every
    # published one, newest first.
    version: str
    state: Literal["in_force", "upcoming", "replaced"]
    current: str
    in_force: str
    versions: list[str]
    sections: list[LegalSectionOut]


class GuideItemOut(BaseModel):
    """A guide article of the site: its title and summary in `language` (English until it's
    translated), and where the site shows it."""

    slug: str
    language: str
    title: str
    description: str
    updated: str
    path: str


class GuideOut(GuideItemOut):
    """A guide article with its Markdown text."""

    body: str


class PageGuideOut(BaseModel):
    """A page's guide: what it's for (`text`), what you can do there, tips, and the guide
    article to read more in, if the page has one."""

    key: str
    title: str
    text: str
    actions: list[str]
    tips: list[str]
    article: GuideItemOut | None = None


class HelpVoteIn(BaseModel):
    """A thumbs up (1) or down (-1) on a help chat answer, null to clear it, with the answer's
    run and signature as its last event gave them."""

    trace_id: str | None = Field(default=None, max_length=TRACE_ID_LENGTH)
    signature: str = Field(max_length=SIGNATURE_LENGTH)
    value: Literal[1, -1] | None
