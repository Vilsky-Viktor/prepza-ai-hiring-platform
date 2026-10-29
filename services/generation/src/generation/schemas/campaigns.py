from pydantic import BaseModel, Field


class CampaignSource(BaseModel):
    """A campaign to translate, sent by notifications: its English texts and the languages it
    lacks."""

    subject: str
    text: str
    button: str | None
    missing: list[str]


class TranslatedCampaign(BaseModel):
    subject: str = Field(description="The email's subject, translated.")
    text: str = Field(description="The email's text, translated, with its paragraphs.")
    button: str = Field(description="The button's text, translated; empty when there's none.")
