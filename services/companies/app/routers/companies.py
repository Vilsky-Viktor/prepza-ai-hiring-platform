from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from prepza_common.analytics import track
from prepza_common.audit_actions import AuditAction, TargetKind
from prepza_common.auth import CurrentUser
from prepza_common.constants import REFERRAL_COOKIE
from prepza_common.human_check import require_human
from prepza_common.limits import at_most, limit
from prepza_common.paging import PageParams
from prepza_common.visitor_country import VisitorCountry

from app.config.settings import settings
from app.constants.invites import (
    COMPANY_NAME_TAKEN,
    EMAIL_NOT_VERIFIED,
    TOO_MANY_COMPANIES,
)
from app.constants.roles import EDITORS, Role
from app.core.exceptions import OverLimit
from app.helpers.brand import color_sets, style_of
from app.helpers.logos import logo_path
from app.integrations import billing
from app.integrations.redis import get_redis
from app.models.companies import Company
from app.schemas.companies import (
    CompanyBalanceOut,
    CompanyCreate,
    CompanyCreditsOut,
    CompanyOut,
    CompanyRename,
    ReferralOut,
    ReferralRewardOut,
)
from app.schemas.logos import BrandColorSets, BrandStyle
from app.service_auth import REQUEST_COMPANY, Via
from app.services import company_deletion, credits
from app.services.access import can_edit, is_owner, require_company, require_editor
from app.services.verification import verify_by_email
from app.storage import audit, companies, interviews

router = APIRouter(prefix="/companies", tags=["companies"])


def company_out(company: Company, user_id: str, interview_count: int = 0) -> CompanyOut:
    member = next(item for item in company.members if item.user_id == user_id)

    return CompanyOut(
        id=company.id,
        name=company.name,
        role=member.role,
        can_edit=can_edit(member),
        can_delete=is_owner(member),
        can_manage_members=is_owner(member),
        can_see_actions=is_owner(member),
        interview_count=interview_count,
        logo_url=logo_path(company),
        brand_colors=company.brand_colors,
        candidate_colors=BrandColorSets(**color_sets(company.brand_colors)),
        brand_style=BrandStyle(**style_of(company)),
        website_domain=company.website_domain,
        verified_domain=company.verified_domain,
        verification_status=company.verification_status,
        decline_reason=company.decline_reason,
        suspended=company.suspended_at is not None,
        ai_apps_allowed=company.ai_apps_off_at is None,
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
    # The welcome credits come once per owner's email: only a verified one may claim them.
    if not user.email_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, EMAIL_NOT_VERIFIED)

    owned = await companies.owned_count(user.uid)

    if owned == 0 and via is None:
        await require_human(request, settings.turnstile_secret_key)

    async def refuse_over(count: int) -> None:
        await at_most(
            get_redis(),
            "MAX_OWNED_COMPANIES",
            count,
            # Waiting won't free one: a quota, not a rate limit.
            status.HTTP_409_CONFLICT,
            TOO_MANY_COMPANIES,
            user_id=user.uid,
        )

    try:
        await refuse_over(owned)
        most = await limit(get_redis(), "MAX_OWNED_COMPANIES")

        try:
            company = await companies.create(body.name, user.uid, user.email, most)
        except OverLimit as over:
            # Another company of theirs was made meanwhile: counted again under its lock.
            await refuse_over(over.count)
            raise
    except HTTPException:
        await track("limit_hit", user_id=user.uid, which="companies_owned")
        raise

    if company is None:
        raise HTTPException(status.HTTP_409_CONFLICT, COMPANY_NAME_TAKEN)

    # When billing still fails after its tries, the company is removed again, so trying again
    # doesn't find its name taken.
    try:
        await billing.welcome_company(
            company.id,
            user.email,
            request.cookies.get(REFERRAL_COOKIE),
            await companies.ids_for_user(user.uid),
            country,
        )
    except Exception:
        await companies.delete(company.id)

        raise

    await track("company_created", user_id=user.uid, company_id=company.id)

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
async def list_companies(user: CurrentUser, page: PageParams) -> list[CompanyOut]:
    """The user's companies; for an AI agent signed in with an API key, the key's only."""
    rows = await companies.list_for_user(
        user.uid, page.offset, page.limit, only=REQUEST_COMPANY.get()
    )
    totals = await interviews.counts([item.id for item in rows])

    return [company_out(item, user.uid, totals.get(item.id, 0)) for item in rows]


@router.get("/credits")
async def list_credits(user: CurrentUser, page: PageParams) -> list[CompanyBalanceOut]:
    """The companies the user may top up, as an owner or admin, with their credits. Declared
    before /{company_id}, which would otherwise take "credits" as an id."""
    rows = await companies.list_for_user(
        user.uid, page.offset, page.limit, EDITORS, REQUEST_COMPANY.get()
    )
    credits = await billing.companies_credits([item.id for item in rows]) if rows else {}

    return [CompanyBalanceOut(id=item.id, name=item.name, **credits[str(item.id)]) for item in rows]


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


@router.get("/{company_id}/referral")
async def get_referral(company_id: UUID, user: CurrentUser) -> ReferralOut:
    """The company's referral link; any member may share it."""
    await require_company(user, company_id)

    found = await billing.company_referral(company_id)
    names = await companies.names([row["company_id"] for row in found["rewards"]])

    return ReferralOut(
        code=found["code"],
        reward=found["reward"],
        rewarded=found["rewarded"],
        rewards=[
            ReferralRewardOut(
                name=names.get(row["company_id"]),
                rewarded_at=row["rewarded_at"],
                credits=row["credits"],
            )
            for row in found["rewards"]
        ],
    )


@router.get("/{company_id}")
async def get_company(company_id: UUID, user: CurrentUser) -> CompanyOut:
    company, member = await require_company(user, company_id)

    # Opening the company is enough: an owner or admin with a work email on its website sends
    # it for review.
    if can_edit(member):
        await verify_by_email(company, user)

    totals = await interviews.counts([company.id])

    return company_out(company, user.uid, totals.get(company.id, 0))


@router.patch("/{company_id}/name", status_code=status.HTTP_204_NO_CONTENT)
async def rename_company(company_id: UUID, body: CompanyRename, user: CurrentUser) -> None:
    """Owners and admins rename the company; names stay unique across prepza, ignoring case."""
    company, _ = await require_editor(user, company_id)
    name = body.title.strip()

    if not name:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Name the company")

    if name == company.name:
        return

    if not await companies.rename(company.id, name):
        raise HTTPException(status.HTTP_409_CONFLICT, COMPANY_NAME_TAKEN)

    await audit.record(
        company.id,
        user.uid,
        AuditAction.COMPANY_RENAMED,
        company.id,
        target_kind=TargetKind.COMPANY,
        target_label=name,
    )
