from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, StringConstraints
from testee_common.auth.user import Language
from testee_common.config.constants import MAX_NEWS_TEXT_LENGTH, MAX_NEWS_TITLE_LENGTH

NewsTitle = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_NEWS_TITLE_LENGTH)
]
NewsText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_NEWS_TEXT_LENGTH)
]


class NewsIn(BaseModel):
    """A post as a superadmin writes it, in English."""

    title: NewsTitle
    text: NewsText
    published_on: date


class NewsOut(BaseModel):
    """A post as the news page shows it, in the reader's language when it's translated."""

    id: UUID
    title: str
    text: str
    published_on: date
    # When the post was last changed, for search engines.
    updated_at: datetime


class AdminNewsOut(NewsOut):
    # Whether every other language has its translation yet.
    translated: bool


class NewsSourceOut(BaseModel):
    """A post's English title and text and the languages it lacks (notifications reads it)."""

    title: str
    text: str
    missing: list[str]


class NewsTitlesIn(BaseModel):
    """Posts the bell names (notifications), and the reader's language."""

    news_ids: list[UUID]
    language: Language


class NewsTitlesOut(BaseModel):
    # By post id; deleted posts are left out.
    titles: dict[str, str]
