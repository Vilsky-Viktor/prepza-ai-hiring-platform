from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.constants.integrity import IntegritySignal
from app.constants.rounds import RoundStatus
from app.schemas.library import TopicQuestions
from app.schemas.review import ReviewItem


class InviteScoresIn(BaseModel):
    invite_ids: list[UUID]


class SetIdsIn(BaseModel):
    set_ids: list[UUID]


class SetCompaniesIn(BaseModel):
    """Each interview's set and its company, by set id (companies' backfill of old sections)."""

    companies: dict[UUID, UUID] = Field(max_length=500)


class InviteIdsIn(BaseModel):
    invite_ids: list[UUID]


class UserIdsOut(BaseModel):
    user_ids: list[str]


class SessionsCreate(BaseModel):
    user_id: str
    candidate_invite_id: UUID
    topics: list[TopicQuestions]
    # Every interview is timed: the seconds each question has.
    question_seconds: int = Field(ge=1)
    # A company member trying their own test (see models/sessions.py).
    preview: bool = False
    # The interview's company, kept on each section.
    company_id: UUID


class SessionTopicOut(BaseModel):
    id: UUID
    topic_title: str
    status: RoundStatus
    total: int
    answered: int


class SessionOut(BaseModel):
    id: UUID
    topic_id: UUID
    # The candidate's invite in companies, which knows the company and its logo.
    candidate_invite_id: UUID
    topic_title: str
    interview_title: str | None = None
    # The language the questions are written in, which can differ from the page's.
    language: str | None = None
    # A talent's practice round: its results page shows every answer.
    practice: bool = False
    status: RoundStatus
    total: int
    answered: int
    started_at: datetime
    finished_at: datetime | None
    # The seconds each question has; None for sessions from before every interview was timed.
    question_seconds: int | None


class SessionAnswerResult(BaseModel):
    answer_id: UUID
    answered: int
    total: int


class ScorecardSession(BaseModel):
    id: UUID
    topic_title: str
    status: RoundStatus
    final_score: int | None
    # Integrity signals: times the candidate left the tab, copy attempts, and answers faster
    # than FAST_ANSWER_SECONDS.
    tab_leaves: int
    copies: int
    fast_answers: int
    review: list[ReviewItem]


class SignalIn(BaseModel):
    kind: IntegritySignal
    # With a return: how long the leave lasted.
    seconds: float | None = Field(default=None, ge=0, le=86_400)
