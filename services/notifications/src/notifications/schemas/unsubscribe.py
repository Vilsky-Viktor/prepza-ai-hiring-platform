from uuid import UUID

from pydantic import BaseModel

from notifications.constants.unsubscribe import UnsubscribeType


class UnsubscribeOut(BaseModel):
    """What a link stops, for the page to say before it's confirmed: the type, and for a
    candidate's link the company's name."""

    type: UnsubscribeType
    company: str | None = None


class CompanyOptOutOut(BaseModel):
    """A company that invited an address, or whose emails it stopped: whether every email from
    the company to it is stopped, whether a superadmin stopped them (only that can be lifted
    there; the candidate's own stops stay), and for how many invites only the reminders are."""

    company_id: str
    name: str
    stopped: bool
    stopped_by_admin: bool
    stopped_reminders: int


class CandidateOptOutsOut(BaseModel):
    companies: list[CompanyOptOutOut]


class CandidateOptOutIn(BaseModel):
    """A superadmin stops a company's emails to the address, or lets them through again."""

    email: str
    company_id: UUID
    stopped: bool
