from uuid import UUID

from pydantic import BaseModel


class ReuseIn(BaseModel):
    embedding: list[float]
    level: str
    language: str
    count: int
    # A company interview's company: companies' shared questions are offered too, never its
    # own. None for a template, which reuses only templates' questions.
    company_id: UUID | None = None
