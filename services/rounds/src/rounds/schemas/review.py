from uuid import UUID

from pydantic import BaseModel


class AnswerView(BaseModel):
    answer_id: UUID
    # The option picked on a single-answer question; None for a multi-answer one, and when a
    # timed question ran out first.
    option_index: int | None
    # Every option picked: the one of a single-answer question, the ones ticked on a
    # multi-answer one; empty when the time ran out.
    picks: list[int] = []
    timed_out: bool = False
    # Of the options picked, how many are right and how many wrong: a multi-answer answer scores
    # only with no wrong one, a share of its points by the right ones; None when the candidate
    # may not see results.
    right_picks: int | None = None
    wrong_picks: int | None = None
    # All points; None when the candidate may not see results.
    correct: bool | None
    # Points out of 100: a share for a multi-answer answer partly right (2 of 3 right options
    # and no wrong one: 67); None when the candidate may not see results.
    score: int | None = None
    # Seconds the answer took; interview answers only.
    seconds: int | None = None
    # Answered faster than FAST_ANSWER_SECONDS.
    fast: bool = False


class ReviewItem(BaseModel):
    """One question of a round. The correct options only once it's answered."""

    question_id: UUID
    number: int
    text: str
    options: list[str]
    # Multi-answer ("select all that apply").
    multi: bool = False
    # The right option of a single-answer question; None for a multi-answer one (see
    # correct_indexes) and before it's answered.
    correct_option_index: int | None
    # Every right option; None before it's answered.
    correct_indexes: list[int] | None = None
    answer: AnswerView | None
    # Interview scorecards only: page leaves and copy attempts while this question was open.
    tab_leaves: int = 0
    copies: int = 0
