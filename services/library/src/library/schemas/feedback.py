from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from library.constants.feedback import MAX_REPORT_COMMENT_LENGTH, ReportReason


class QuestionRatingIn(BaseModel):
    value: Literal[-1, 1]


class QuestionRatingOut(BaseModel):
    value: Literal[-1, 1] | None = None


class ReportIn(BaseModel):
    reason: ReportReason
    comment: str = Field(default="", max_length=MAX_REPORT_COMMENT_LENGTH)

    @model_validator(mode="after")
    def require_comment_for_other(self) -> "ReportIn":
        if self.reason is ReportReason.OTHER and not self.comment.strip():
            raise ValueError("Details are required for this reason.")

        return self


class InternalRatingIn(QuestionRatingIn):
    user_id: str


class InternalReportIn(ReportIn):
    user_id: str


class MyReportOut(BaseModel):
    reported: bool


class ReportOut(BaseModel):
    """A report without the reporter's identity."""

    id: UUID
    reason: str
    # Empty for a replaced question's kept reports: their comments aren't kept.
    comment: str
    created_at: datetime
