"""The payload of `news.translated`: generation translated a news post (its outbox, from the batch
that translated it) and site saves the translations, only while the post still reads as `title`
and `text`. Site's subscription takes the `news.` family (its filter is far from Pub/Sub's 256
bytes). A payload that fails validation can never be handled (dropped by handle_or_drop)."""

from uuid import UUID

from prepza_common.auth.user import Language
from prepza_common.config.constants import MAX_NEWS_TEXT_LENGTH, MAX_NEWS_TITLE_LENGTH
from pydantic import BaseModel, ConfigDict, Field

NEWS_TRANSLATED = "news.translated"


class NewsTranslation(BaseModel):
    """A post in one language."""

    title: str = Field(min_length=1, max_length=MAX_NEWS_TITLE_LENGTH)
    text: str = Field(min_length=1, max_length=MAX_NEWS_TEXT_LENGTH)


class NewsTranslated(BaseModel):
    """The English title and text the translations are of, and the translations by language."""

    model_config = ConfigDict(extra="ignore")

    news_id: UUID
    title: str
    text: str
    translations: dict[Language, NewsTranslation]
