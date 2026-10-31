"""The payload of companies' `interview.privacy_changed`: an interview's questions kept out of
testee's shared question bank (`keep_private`) or let back in. Library, which holds the bank,
consumes it; the newest `changed_at` wins, whatever order the events come in. Consumers ignore
fields they don't know (tolerant reader)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

INTERVIEW_PRIVACY_CHANGED = "interview.privacy_changed"


class InterviewPrivacyChanged(BaseModel):
    """Its questions' set (none while it's still generating) and its generation, so library
    finds the set by either."""

    model_config = ConfigDict(extra="ignore")

    interview_id: UUID
    company_id: UUID
    set_id: UUID | None = None
    generation_id: UUID | None = None
    keep_private: bool
    changed_at: datetime
