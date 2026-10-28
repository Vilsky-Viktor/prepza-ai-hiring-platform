from datetime import datetime

from pydantic import BaseModel


class AccountOut(BaseModel):
    """A prepza account, for the admin zone's support tab: `email` is None for an account
    without one (a company's guest candidate), `created_at` when Firebase doesn't say."""

    user_id: str
    email: str | None
    created_at: datetime | None
