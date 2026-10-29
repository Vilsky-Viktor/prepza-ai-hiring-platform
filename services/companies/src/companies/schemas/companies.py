from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from prepza_common.i18n.titles import at_least
from pydantic import AfterValidator, BaseModel, EmailStr, Field

from companies.constants.invites import (
    COMPANY_NAME_TOO_SHORT,
    MAX_COMPANY_NAME_LENGTH,
    MIN_COMPANY_NAME_LENGTH,
)
from companies.constants.roles import Role
from companies.constants.verification import VerificationStatus
from companies.schemas.logos import BrandColorSets, BrandStyle, SavedBrandColors

# A company's name, as an owner or admin gives it or a superadmin corrects it.
CompanyName = Annotated[
    str,
    Field(max_length=MAX_COMPANY_NAME_LENGTH),
    AfterValidator(at_least(MIN_COMPANY_NAME_LENGTH, COMPANY_NAME_TOO_SHORT)),
]


class CompanyCreate(BaseModel):
    name: CompanyName


class CompanyRename(BaseModel):
    """A new name, edited in place like a test's title (hence `title`)."""

    title: CompanyName


class MemberOut(BaseModel):
    id: UUID
    email: str
    role: str
    joined: bool
    token: str | None = None
    # Whether the user can remove this member or pending invite, or change its role: the owner,
    # any row but their own.
    removable: bool = False
    # Whether the user can make this member the owner: the owner, for a joined admin.
    can_own: bool = False
    created_at: datetime


class AdminInviteOut(BaseModel):
    """What the invited member sees before accepting."""

    company_name: str
    # Only for the signed-in account it was sent to, with its email verified.
    email: str | None = None
    # Whether it was sent to the signed-in account's email: they may join with it.
    matches: bool = False
    joined: bool
    # Only for the member who joined through this link, so they can open the company.
    company_id: UUID | None = None


class CompanyOut(BaseModel):
    id: UUID
    name: str
    role: str
    # Owners and admins change things and spend credits; viewers only look and share reports.
    can_edit: bool
    # Only the owner deletes the company, and adds, removes and changes the roles of its members.
    can_delete: bool
    can_manage_members: bool
    # Only the owner sees the company's action log.
    can_see_actions: bool = False
    interview_count: int
    # Its team as the Team page counts it (members and pending invites).
    member_count: int = 0
    # The logo's address on the site; None until one is set.
    logo_url: str | None = None
    # Its own colors on candidates' pages, by theme (a theme missing: prepza's), and the colors
    # those pages use, by theme: its own, or prepza's.
    brand_colors: SavedBrandColors | None = None
    candidate_colors: BrandColorSets | None = None
    # Why a theme's saved colors are refused now, by theme, in the user's language (a check added
    # since they were saved); its candidates see prepza's colors for that theme until they change.
    brand_problems: dict[str, str] = {}
    # Its fonts (titles and text) and corner rounding on those pages, prepza's where it set none.
    brand_style: BrandStyle | None = None
    # The website's domain, and the same once a superadmin approved it (the badge); where its
    # verification stands, and why it was declined, when the superadmin said.
    website_domain: str | None = None
    verified_domain: str | None = None
    verification_status: VerificationStatus = VerificationStatus.NONE
    decline_reason: str | None = None
    # A superadmin suspended it: its members can read, not change it.
    suspended: bool = False
    # Members may use its data from AI apps they connected.
    ai_apps_allowed: bool = True
    # The sites that may embed its interviews with the SDK, and whether localhost may too
    # (schemas/allowed_domains.py).
    allowed_domains: list[str] = []
    allow_localhost: bool = False
    created_at: datetime


# The roles the owner gives a member.
MemberRole = Literal[Role.ADMIN, Role.VIEWER]


class MemberIn(BaseModel):
    email: EmailStr
    role: MemberRole = Role.ADMIN


class MemberRoleIn(BaseModel):
    role: MemberRole


class ReferralRewardOut(BaseModel):
    """A company that came through the link and topped up; no name once it's deleted."""

    name: str | None
    rewarded_at: datetime
    # The credits it gave this company then.
    credits: int


class ReferralOut(BaseModel):
    """The company's referral link code, what it earns, how many it has earned for, and the latest
    of those, newest first."""

    code: str
    reward: int
    rewarded: int
    rewards: list[ReferralRewardOut]


class MenuCountsOut(BaseModel):
    """How many things each of the company's menu pages holds; None for a part another service
    couldn't give in time, which the menu then shows without."""

    interviews: int
    # Joined members and pending invites, as the Team page lists them.
    members: int
    integrations: int | None
    referrals: int | None


class CompanyCreditsOut(BaseModel):
    available: int
    # Set aside for candidates invited who haven't finished.
    reserved: int = 0
    # How many candidates those are.
    reserved_candidates: int = 0
    low: bool
    # Candidates the available credits pay for (billing works it out).
    candidates: int = 0


class CompanyBalanceOut(BaseModel):
    """A company the user can top up, with its credits."""

    id: UUID
    name: str
    available: int
    low: bool


class UserCompaniesOut(BaseModel):
    """Every company the user is a member of, for the notifications service."""

    company_ids: list[str]
