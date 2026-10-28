from pydantic import BaseModel


class LimitsOut(BaseModel):
    """The current limits the site's texts quote: the most emails one list may invite."""

    max_bulk_invites: int
