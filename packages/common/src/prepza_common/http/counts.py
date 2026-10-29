from pydantic import BaseModel


class CountOut(BaseModel):
    """How many of something a service holds, for another service's internal call (a company's
    working integrations, for its menu)."""

    count: int
