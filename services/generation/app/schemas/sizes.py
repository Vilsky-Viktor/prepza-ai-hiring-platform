from pydantic import BaseModel


class SizesOut(BaseModel):
    """How big a new interview is made, as set in the admin zone's Controls."""

    # Questions written for each topic of a company's interview.
    questions_per_topic: int
