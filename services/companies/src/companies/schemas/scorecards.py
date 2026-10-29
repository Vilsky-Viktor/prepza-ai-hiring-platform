"""A candidate's scorecard: their invite and overall result from companies, and each section
with its questions and answers from rounds."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from companies.schemas.answer_patterns import AnswerPatterns


class ScorecardAnswer(BaseModel):
    answer_id: UUID
    # The option picked on a single-answer question; None for a multi-answer one, and when a
    # timed question ran out first.
    option_index: int | None
    # Every option picked (several on a multi-answer question); empty when the time ran out.
    picks: list[int] = []
    timed_out: bool = False
    # Of the options picked, how many are right and how many wrong.
    right_picks: int | None = None
    wrong_picks: int | None = None
    # All points.
    correct: bool | None
    # Points out of 100: a share for a multi-answer answer partly right.
    score: int | None = None
    seconds: int | None = None
    # Answered faster than rounds' FAST_ANSWER_SECONDS.
    fast: bool = False


class ScorecardQuestion(BaseModel):
    question_id: UUID
    number: int
    text: str
    options: list[str]
    # Multi-answer ("select all that apply").
    multi: bool = False
    # The question's own time (rounds fits it to the interview's average); None when untimed.
    limit_seconds: int | None = None
    # Only once the question is answered: the right option of a single-answer question, and
    # every right option.
    correct_option_index: int | None
    correct_indexes: list[int] | None = None
    answer: ScorecardAnswer | None
    # Page leaves and copy attempts while this question was open.
    tab_leaves: int = 0
    copies: int = 0


class ScorecardSection(BaseModel):
    """One topic's round."""

    id: UUID
    topic_title: str
    status: str
    final_score: int | None
    tab_leaves: int
    copies: int
    fast_answers: int
    review: list[ScorecardQuestion]
    # None while the section is still going.
    passed: bool | None


class ScorecardOut(BaseModel):
    id: UUID
    email: str
    # The name from the candidate's sign-in; None until they start, or when it has none.
    name: str | None = None
    status: str
    extra_time: int
    # Whether the user may change the candidate (extra time, revoke): not a viewer.
    can_edit: bool
    # What the candidate's actions offer (helpers/candidates.py row_actions).
    can_resend: bool = False
    revokable: bool = False
    # What extra time can still be given: only before the candidate starts, and not by a viewer.
    extra_time_options: list[int]
    # The invite link's token, to copy and send in case the email didn't arrive or got lost: until
    # the candidate finishes, while the link works (not expired), and not for a viewer.
    invite_token: str | None = None
    # For the PDF report: the test, the company, and the overall result.
    title: str | None
    company: str
    logo_url: str | None
    verified_domain: str | None
    grade: int | None
    # None until the candidate finishes.
    passed: bool | None
    pass_mark: int
    # The language the questions are written in, which can differ from the page's.
    language: str
    # When the candidate confirmed they'd answer on their own, without AI tools or other people;
    # None before they start (and for candidates from before it was asked).
    pledged_at: datetime | None = None
    sessions: list[ScorecardSection]
    # The integrity signals the answers and times show over every section (empty when none
    # fired) and questions to ask in a live interview; both empty until the candidate finishes.
    answer_patterns: AnswerPatterns = AnswerPatterns()
