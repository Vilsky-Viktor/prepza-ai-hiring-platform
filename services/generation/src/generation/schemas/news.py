from pydantic import BaseModel, Field


class NewsSource(BaseModel):
    """A post to translate, sent by site: its English title and text and the languages it lacks."""

    title: str
    text: str
    missing: list[str]


class TranslatedNews(BaseModel):
    title: str = Field(description="The post's title, translated.")
    text: str = Field(description="The post's text, translated, with its line breaks.")
