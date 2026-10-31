from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from testee_common.auth.auth import CurrentUser
from testee_common.db.paging import PageParams
from testee_common.http.visitor_country import VisitorCountry
from testee_common.i18n.i18n import request_language

from companies.api.dependencies import Via
from companies.constants.roles import Role
from companies.core.db import Session
from companies.helpers.brand import brand_problems, color_sets, style_of
from companies.helpers.logos import logo_path
from companies.models.companies import Company
from companies.repositories import interviews
from companies.schemas.companies import (
    CompanyBalanceOut,
    CompanyCreate,
    CompanyCreditsOut,
    CompanyOut,
    CompanyRename,
    MenuCountsOut,
    ReferralOut,
    ReferralRewardOut,
)
from companies.schemas.logos import BrandColorSets, BrandStyle
from companies.services import (
    company_creation,
    company_deletion,
    company_settings,
    company_views,
    credits,
    menu_counts,
)
from companies.services.access import (
    can_edit,
    is_owner,
    member_of,
    require_company,
    require_editor,
)
from companies.services.verification import verify_by_email

router = APIRouter(prefix="/companies", tags=["companies"])


def company_out(
    company: Company, user_id: str, language: str, interview_count: int = 0
) -> CompanyOut:
    member = member_of(company, user_id)

    return CompanyOut(
        id=company.id,
        name=company.name,
        role=member.role,
        can_edit=can_edit(member),
        can_delete=is_owner(member),
        can_manage_members=is_owner(member),
        can_see_actions=is_owner(member),
        interview_count=interview_count,
        member_count=len(company.members),
        logo_url=logo_path(company),
        brand_colors=company.brand_colors,
        candidate_colors=BrandColorSets(**color_sets(company.brand_colors)),
        brand_problems=brand_problems(company.brand_colors, language),
        brand_style=BrandStyle(**style_of(company)),
        website_domain=company.website_domain,
        verified_domain=company.verified_domain,
        verification_status=company.verification_status,
        decline_reason=company.decline_reason,
        suspended=company.suspended_at is not None,
        ai_apps_allowed=company.ai_apps_off_at is None,
        # A company not yet saved has no defaults filled in.
        allowed_domains=company.allowed_domains or [],
        allow_localhost=bool(company.allow_localhost),
        created_at=company.created_at,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_company(
    body: CompanyCreate,
    user: CurrentUser,
    request: Request,
    via: Via,
    country: VisitorCountry = None,
) -> CompanyOut:
    """A company needs its owner's verified email, as the welcome credits come once per email. A
    person's first company, which gets them, needs them to show they're a person, on the site;
    through the assistant or an AI app (no browser) it can't be asked."""
    company = await company_creation.create(body.name, user, request, via, country)

    return CompanyOut(
        id=company.id,
        name=company.name,
        role=Role.OWNER,
        can_edit=True,
        can_delete=True,
        can_manage_members=True,
        can_see_actions=True,
        interview_count=0,
        created_at=company.created_at,
    )


@router.get("")
async def list_companies(user: CurrentUser, page: PageParams, request: Request) -> list[CompanyOut]:
    """The user's companies; for an AI agent signed in with an API key, the key's only."""
    rows = await company_views.listed(user.uid, page.offset, page.limit)

    language = request_language(request)

    return [company_out(item, user.uid, language, count) for item, count in rows]


@router.get("/credits")
async def list_credits(user: CurrentUser, page: PageParams) -> list[CompanyBalanceOut]:
    """The companies the user may top up, as an owner or admin, with their credits. Declared
    before /{company_id}, which would otherwise take "credits" as an id."""
    rows = await company_views.with_credits(user.uid, page.offset, page.limit)

    return [CompanyBalanceOut(id=item.id, name=item.name, **credits) for item, credits in rows]


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(company_id: UUID, user: CurrentUser) -> None:
    """Only the owner can do it."""
    _, member = await require_company(user, company_id)

    if not is_owner(member):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the owner can remove the company")

    await company_deletion.delete_company(company_id)


@router.get("/{company_id}/credits")
async def get_credits(company_id: UUID, user: CurrentUser) -> CompanyCreditsOut:
    """Candidates the company can still invite; any member may see it."""
    await require_company(user, company_id)

    return await credits.credits_of(company_id)


@router.get("/{company_id}/menu-counts")
async def get_menu_counts(company_id: UUID, user: CurrentUser) -> MenuCountsOut:
    """How many things each of the company's menu pages holds; any member sees them."""
    company, _ = await require_company(user, company_id)

    return await menu_counts.menu_counts(company, user.uid)


@router.get("/{company_id}/referral")
async def get_referral(company_id: UUID, user: CurrentUser) -> ReferralOut:
    """The company's referral link; any member may share it."""
    await require_company(user, company_id)

    found = await company_views.referral(company_id)

    return ReferralOut(
        code=found["code"],
        reward=found["reward"],
        rewarded=found["rewarded"],
        rewards=[
            ReferralRewardOut(
                name=found["names"].get(row["company_id"]),
                rewarded_at=row["rewarded_at"],
                credits=row["credits"],
            )
            for row in found["rewards"]
        ],
    )


@router.get("/{company_id}")
async def get_company(company_id: UUID, user: CurrentUser, request: Request) -> CompanyOut:
    company, member = await require_company(user, company_id)

    # Opening the company is enough: an owner or admin with a work email on its website sends
    # it for review.
    if can_edit(member):
        await verify_by_email(company, user)

    async with Session() as session:
        totals = await interviews.counts(session, [company.id])

    return company_out(company, user.uid, request_language(request), totals.get(company.id, 0))


@router.patch("/{company_id}/name", status_code=status.HTTP_204_NO_CONTENT)
async def rename_company(company_id: UUID, body: CompanyRename, user: CurrentUser) -> None:
    """Owners and admins rename the company; names stay unique across testee, ignoring case."""
    company, _ = await require_editor(user, company_id)
    await company_settings.rename(company, user.uid, body.title)
