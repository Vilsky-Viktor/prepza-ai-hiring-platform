from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field
from testee_common.auth.user import Language
from testee_common.config.constants import MAX_GOAL_LENGTH
from testee_common.i18n.titles import Title

from companies.constants.interviews import (
    MAX_PASS_MARK,
    MAX_QUESTION_SECONDS,
    MIN_PASS_MARK,
    MIN_QUESTION_SECONDS,
)


class InterviewCreate(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_GOAL_LENGTH)
    # The language to generate the interview in; none means the job description's own.
    generate_in: Language | None = None


class InterviewFromTemplate(BaseModel):
    template_id: UUID


class PreviewOut(BaseModel):
    """The first session of a member's preview, to open in the player."""

    session_id: UUID


class InterviewOut(BaseModel):
    id: UUID
    # None for a test made from a template.
    generation_id: UUID | None
    set_id: UUID | None
    # Without a set: its generation failed and waits for a retry; otherwise it's generating.
    generation_failed: bool
    title: str | None
    question_seconds: int
    candidate_count: int
    hired: bool
    pass_mark: int
    # The shareable link's code while it's on.
    link_token: str | None
    # New, in process or hired (constants/interviews.py).
    status: str
    created_at: datetime
    # When it last changed; the API syncs lists by it (updated_since).
    updated_at: datetime | None = None
    # Its team's notes: how many, and the pinned one's text (None without one).
    note_count: int = 0
    pinned_note: str | None = None
    # Taken in voice mode (read aloud, answered by voice); click mode otherwise, the default.
    voice: bool = False


class QuestionOption(BaseModel):
    answer: str
    correct: bool


class QuestionText(BaseModel):
    """A question as the company manages it: text, answer options and feedback counts."""

    id: UUID
    text: str
    options: list[QuestionOption]
    # Multi-answer ("select all that apply"): more than one option is right.
    multi: bool = False
    likes: int
    dislikes: int
    reports: int


class ReportOut(BaseModel):
    id: UUID
    reason: str
    comment: str
    created_at: datetime


class TopicOut(BaseModel):
    id: UUID
    title: str
    subtopics: list[str] = []
    question_count: int
    # Questions each candidate gets from the topic.
    question_limit: int


class InterviewDetail(InterviewOut):
    # The company it belongs to, so a link to it can be built from the interview alone.
    company_id: UUID
    # The language its topics and questions are written in, which can differ from the page's.
    language: str
    topics: list[TopicOut]
    # The whole interview at its time per question, in minutes, as a candidate sees it before
    # starting; None while its questions aren't known.
    total_minutes: int | None = None
    # Every question a candidate gets, over all topics; None while its questions aren't known.
    total_questions: int | None = None
    # The most questions a candidate may get over all topics (the topics tab shows the total
    # against it).
    max_questions: int
    # Whether the user may change the test and its candidates: owners and admins, not viewers.
    can_edit: bool = False
    # Its questions are kept out of testee's shared question bank (the terms' opt-out).
    keep_private: bool = False
    # Whether its language allows voice mode (VOICE_LANGUAGES, listed for the setting's note).
    voice_available: bool = False
    voice_languages: list[str] = []
    # Whether the company may use the Discover tab: it has topped up at least once.
    discover: bool = False


class ReviewIn(BaseModel):
    """Topic indices to keep, and optional free-text changes, as the generation service takes them."""

    selected: list[int] = Field(min_length=1)
    instructions: str = ""
    # Every drafted topic with the reviewer's own edits; generation validates it.
    topics: list[dict] | None = None


class TopicLimitIn(BaseModel):
    # The topic's whole size gives every candidate every question; 0 leaves the topic out.
    limit: int = Field(ge=0)


class InterviewSettings(BaseModel):
    """A change to a test's settings: only the ones sent change; the others stay as they are."""

    question_seconds: int | None = Field(
        default=None, ge=MIN_QUESTION_SECONDS, le=MAX_QUESTION_SECONDS
    )
    hired: bool | None = None
    pass_mark: int | None = Field(default=None, ge=MIN_PASS_MARK, le=MAX_PASS_MARK)
    keep_private: bool | None = None
    voice: bool | None = None


class TitleIn(BaseModel):
    title: Title
