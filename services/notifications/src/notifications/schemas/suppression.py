from datetime import datetime

from pydantic import BaseModel


class SuppressionOut(BaseModel):
    """The address's place on the suppression list; both None when it isn't on it."""

    reason: str | None
    created_at: datetime | None
