from pydantic import BaseModel, Field


class ConversationTitle(BaseModel):
    title: str = Field(description="The conversation's title: a few words, one line.")
