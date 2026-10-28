from uuid import UUID

from pydantic import BaseModel, Field


class NewsSource(BaseModel):
    """A post to translate, from the library: its English text and the languages it lacks."""

    title: str
    text: str
    missing: list[str]


class TranslatedNews(BaseModel):
    title: str = Field(description="The post's title, translated.")
    text: str = Field(description="The post's text, translated, with its line breaks.")


class TranslateNews(BaseModel):
    news_id: UUID
