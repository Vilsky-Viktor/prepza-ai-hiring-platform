from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, EmailStr, Field, StringConstraints

from app.constants.brand import Theme
from app.constants.invites import (
    EXTRA_TIME_OPTIONS,
    MAX_BULK_TEXT_LENGTH,
    MAX_CANDIDATE_NAME_LENGTH,
)
from app.schemas.logos import BrandColorSets, BrandStyle


class CandidateIn(BaseModel):
    email: EmailStr
    # Optional; trimmed and cut to MAX_CANDIDATE_NAME_LENGTH as it's saved.
    name: str | None = None


class SectionGrade(BaseModel):
    title: str
    # None until the section is finished.
    grade: int | None = None


class CandidateOut(BaseModel):
    id: UUID
    email: str
    # The name from the candidate's sign-in; None until they start, or when it has none.
    name: str | None = None
    status: str
    progress: int = 0
    grade: int | None = None
    # None until the candidate finishes.
    passed: bool | None = None
    # Integrity signals: page leaves, copy attempts and answers picked too fast to have read.
    tab_leaves: int = 0
    copies: int = 0
    fast_answers: int = 0
    # Too many integrity signals to trust the result, as the ATS integrations are told.
    flagged: bool = False
    # Extra time per question, as a percentage of its time.
    extra_time: int = 0
    created_at: datetime
    # When it last changed; the API syncs lists by it (updated_since).
    updated_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    # The invite link's token, only for the public API (`with_link`): until the candidate
    # finishes, while the link works.
    invite_token: str | None = None
    # What its row offers: sending the invite again (not once finished, nor erased), and whether
    # removing it revokes an invite not used yet (else it erases a candidate who started).
    can_resend: bool = False
    revokable: bool = False
    # Each section's grade, only for one candidate through the public API.
    sections: list[SectionGrade] | None = None


class CompanyCandidateOut(CandidateOut):
    """A candidate found across the company's interviews, with the interview they're in."""

    interview_id: UUID
    interview_title: str | None


class InviteView(BaseModel):
    interview_id: UUID
    title: str | None
    company: str
    logo_url: str | None = None
    # The company's verified domain, for the badge beside its name.
    verified_domain: str | None = None
    # Only for the signed-in account it was sent to, with its email verified.
    email: str | None = None
    # Whether it was sent to the signed-in account's email: they may start it with it.
    matches: bool = False
    status: str
    # Shown before the candidate starts: the timer begins at start.
    question_seconds: int
    # The whole interview at that pace, in minutes; None while its questions aren't known.
    total_minutes: int | None = None
    # Sent by the company's own platform: the link signs the candidate in, no account needed.
    guest: bool = False
    # The interview's colors by theme, and the theme the invite asked for (None: the
    # candidate's own).
    brand_colors: BrandColorSets | None = None
    theme: Theme | None = None
    brand_style: BrandStyle | None = None
    # The website that may embed this interview in a frame (with its subdomains): the company's
    # verified one (a superadmin approved it), for a guest invite only. None: no site may.
    embed_domain: str | None = None


class SessionSummary(BaseModel):
    id: UUID
    topic_title: str
    status: str


class StartIn(BaseModel):
    """Starting an interview (an invite, a shareable link or a member's preview)."""

    # The candidate confirmed they'll answer on their own, without AI tools or other people.
    pledged: bool = False


class InviteStartOut(BaseModel):
    sessions: list[SessionSummary]


class LinkView(BaseModel):
    """What a test's shareable link shows before anyone starts."""

    title: str | None
    company: str
    logo_url: str | None = None
    verified_domain: str | None = None
    # The test's colors by theme (the candidate's own theme picks which), font and rounding.
    brand_colors: BrandColorSets | None = None
    brand_style: BrandStyle | None = None
    question_seconds: int
    # The whole test at that pace, in minutes; None while its questions aren't known.
    total_minutes: int | None = None
    # The signed-in person's invite status for this test; None before they start it.
    status: str | None = None


class LinkIn(BaseModel):
    on: bool


class LinkOut(BaseModel):
    """The test's shareable link code, or None while it's off."""

    link_token: str | None


class CandidateFiltersOut(BaseModel):
    """What a company can narrow its candidates to: statuses and results."""

    filters: list[str]


class BulkInviteIn(BaseModel):
    """A list of emails as pasted or read from a file; any other text around them is ignored."""

    # Its limit is checked with its own message (helpers/list_files.py); this only caps the body.
    text: str = Field(min_length=1, max_length=4 * MAX_BULK_TEXT_LENGTH)
    # The form's name field, for a text with one email; trimmed and cut as it's saved.
    name: str | None = None
    # The uploaded file's name, when the text was read from one.
    filename: str | None = Field(default=None, max_length=255)


class SkippedInvite(BaseModel):
    email: str
    # constants/invites.py SkipReason.
    reason: str


class LineProblemOut(BaseModel):
    """A line of the list that couldn't be used, as it was written, and why (LineProblem)."""

    line: str
    reason: str


class BulkInviteOut(BaseModel):
    invited: list[str]
    skipped: list[SkippedInvite]
    # Every line that couldn't be used, in the list's order: nobody on it was invited.
    problems: list[LineProblemOut] = []


def _offered(value: int) -> int:
    if value not in EXTRA_TIME_OPTIONS:
        raise ValueError(f"Extra time must be one of {EXTRA_TIME_OPTIONS}")

    return value


# Extra time for a candidate who needs it, in percent of each question's time.
ExtraTime = Annotated[int, AfterValidator(_offered)]
# A candidate's name as an owner or admin corrects it, trimmed; blank means not known.
CandidateName = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=MAX_CANDIDATE_NAME_LENGTH)
]


class ExtraTimeIn(BaseModel):
    """Extra time for a candidate who needs it, in percent of each question's time."""

    extra_time: ExtraTime


class CandidateNameIn(BaseModel):
    """A candidate's name as an owner or admin corrects it; blank means not known."""

    name: CandidateName


class CandidateChangesIn(BaseModel):
    """An API key's changes to a candidate, made all or none: only the fields given."""

    name: CandidateName | None = None
    extra_time: ExtraTime | None = None


class InvitedCompaniesOut(BaseModel):
    """The companies that invited an address, for the notifications service."""

    company_ids: list[str]


class GuestTokenOut(BaseModel):
    # A Firebase custom token for the invite's guest.
    token: str
