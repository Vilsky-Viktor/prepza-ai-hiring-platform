from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from rounds.constants.rounds import OPTIONS_PER_QUESTION


class AnswerCreate(BaseModel):
    """The option picked on a single-answer question, or the options ticked on a multi-answer
    one ("select all that apply")."""

    question_id: UUID
    option_index: int | None = Field(default=None, ge=0, lt=OPTIONS_PER_QUESTION)
    picks: list[int] | None = Field(default=None, min_length=1, max_length=OPTIONS_PER_QUESTION)

    @model_validator(mode="after")
    def one_answer(self):
        if (self.option_index is None) == (self.picks is None):
            raise ValueError("Send either option_index or picks")

        if self.picks is not None and (
            len(set(self.picks)) != len(self.picks)
            or any(not 0 <= pick < OPTIONS_PER_QUESTION for pick in self.picks)
        ):
            raise ValueError("Picks must be distinct options")

        return self

    def picked(self) -> list[int]:
        """The options chosen, in order."""
        return sorted(self.picks) if self.picks is not None else [self.option_index]


class NextQuestion(BaseModel):
    """The next unanswered question, without the correct flags."""

    question_id: UUID
    number: int
    text: str
    options: list[str]
    # Multi-answer ("select all that apply"): the candidate ticks every right option; how many
    # are right is never said.
    multi: bool = False
    # Timed interviews only: seconds until the question counts as wrong. Relative, so the
    # candidate's clock being off doesn't matter.
    seconds_left: float | None = None
