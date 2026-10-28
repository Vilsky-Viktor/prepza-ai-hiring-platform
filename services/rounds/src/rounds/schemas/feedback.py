from typing import Literal

from pydantic import BaseModel


class RatingIn(BaseModel):
    value: Literal[-1, 1]


class ReportIn(BaseModel):
    reason: str
    comment: str = ""
