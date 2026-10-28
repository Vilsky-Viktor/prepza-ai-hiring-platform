from pydantic import BaseModel


class TranscriptOut(BaseModel):
    text: str
