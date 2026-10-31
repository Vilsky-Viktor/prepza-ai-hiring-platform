from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from testee_common.ai.sets import OptionIn

from library.schemas.preparations import TopicOut


class TemplateSummary(BaseModel):
    """A template in the admin's list."""

    id: UUID
    slug: str | None
    title: str
    level: str
    language: str
    topic_count: int
    created_at: datetime
    # When its title last changed; a sitemap's "last modified".
    updated_at: datetime
    # Whether search engines should index its public pages (helpers/templates.py).
    indexable: bool = False


class TemplateCopyIn(BaseModel):
    company_id: str


class TemplateCopyOut(BaseModel):
    """The company's new test set."""

    id: UUID
    title: str
    language: str
    # basic, medium or hard: the test's seconds a question come from it.
    level: str


class TemplateFiltersOut(BaseModel):
    """What the template list can be filtered by."""

    levels: list[str]
    languages: list[str]


class TemplateOut(TemplateSummary):
    topics: list[TopicOut]


class SampleQuestionOut(BaseModel):
    """A practice question of a template, with its answer, shown on its public practice page."""

    id: UUID
    topic: str
    text: str
    options: list[OptionIn]


class PoolTopicOut(BaseModel):
    """A template topic as its superadmin page shows it: its questions by pool."""

    id: UUID
    title: str
    subtopics: list[str]
    practice_count: int
    company_count: int


class PooledTemplateOut(TemplateSummary):
    topics: list[PoolTopicOut]
    # Whether a topic lacks practice or company questions, so a top-up has something to write.
    short: bool
