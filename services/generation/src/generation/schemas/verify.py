from pydantic import BaseModel, Field

from generation.constants.quality import QualityFlag
from generation.schemas.regenerate import RegeneratedOption


class VerifyIn(BaseModel):
    flag: QualityFlag
    # A superadmin's "Fix now": a wrong key is checked at once, not in the next batch.
    now: bool = False


class ReportNote(BaseModel):
    reason: str
    comment: str


class QuestionQuality(BaseModel):
    text: str
    options: list[RegeneratedOption]
    answers: int
    option_picks: dict[str, int]
    reports: list[ReportNote]
    # The flag the library has now; None once the question was kept or replaced since.
    flag: QualityFlag | None = None


class KeyCheck(BaseModel):
    correct_indexes: list[int] | None = Field(
        description="The numbers of the options that are correct, as the question's kind asks: "
        "one for a single-answer question, 2 or 3 for a select-all-that-apply one. Null "
        "when no such answer can be given with certainty."
    )


class SelfCheck(KeyCheck):
    """A new multi-answer question's self-check: its key, found blind, and any condition left
    open that decides an option (prompts/self_check.py)."""

    open_condition: str | None = Field(
        description="A few words naming an unstated condition that decides whether some option "
        "is right or wrong, or null when there is none."
    )
