from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.constants.brand import Theme


class AccessOut(BaseModel):
    # Any member (owner, admin or viewer); an editor is an owner or admin.
    member: bool
    editor: bool
    # Why any request of theirs is refused (403), as companies' own routes refuse it: an AI app
    # while the company doesn't allow them, an API key's agent in another company.
    refused: str | None = None
    # Why a change is refused (403) though they may read: the company is suspended.
    read_only: str | None = None


class InterviewBriefOut(BaseModel):
    id: UUID
    company_id: UUID
    title: str | None
    # It has its questions, so candidates can be invited.
    ready: bool


class AtsInviteIn(BaseModel):
    email: EmailStr
    # Whoever connected the ATS: the invite is sent as them, under their email limits.
    sender_id: str
    # The candidate's name from the ATS or the API caller, if any: it fills a name not known yet.
    name: str | None = None
    # The API caller's: where to take the candidate back once they've finished, and whether
    # prepza emails them (no invite or reminders when the caller sends them itself).
    return_url: str | None = Field(default=None, max_length=2048)
    # The theme the candidate's pages show; None: the candidate's own.
    theme: Theme | None = None
    sign_in: bool = True
    # False (the API): a candidate whose invite is still open is returned as they are, without
    # another email, so a retried request invites once; an ATS sends the invite again.
    resend: bool = True


class AtsInviteOut(BaseModel):
    invite_id: UUID
    # Whether this request invited them (or invited them again).
    created: bool = True
