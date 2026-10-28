from pydantic import BaseModel


class ReuseIn(BaseModel):
    embedding: list[float]
    level: str
    language: str
    count: int
