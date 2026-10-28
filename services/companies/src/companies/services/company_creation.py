from fastapi import HTTPException, Request, status
from prepza_common.auth.auth import CurrentUser
from prepza_common.auth.human_check import require_human
from prepza_common.config.constants import REFERRAL_COOKIE
from prepza_common.events.analytics import track
from prepza_common.limits.limits import at_most, limit
from sqlalchemy.exc import IntegrityError

from companies.config import settings
from companies.constants.invites import COMPANY_NAME_TAKEN, EMAIL_NOT_VERIFIED, TOO_MANY_COMPANIES
from companies.core.db import Session
from companies.core.exceptions import OverLimit
from companies.integrations import billing
from companies.integrations.redis import get_redis
from companies.models.companies import Company
from companies.repositories import companies
from companies.services.company_deletion import delete_rows


async def create(
    name: str, user: CurrentUser, request: Request, via: str | None, country: str | None
) -> Company:
    """A company needs its owner's verified email, as the welcome credits come once per email. A
    person's first company, which gets them, needs them to show they're a person, on the site;
    through the assistant or an AI app (no browser) it can't be asked."""
    # The welcome credits come once per owner's email: only a verified one may claim them.
    if not user.email_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, EMAIL_NOT_VERIFIED)

    async with Session() as session:
        owned = await companies.owned_count(session, user.uid)

    if owned == 0 and via is None:
        await require_human(request, settings.turnstile_secret_key)

    try:
        company = await save(name, user, owned)
    except HTTPException:
        await track("limit_hit", user_id=user.uid, which="companies_owned")
        raise

    if company is None:
        raise HTTPException(status.HTTP_409_CONFLICT, COMPANY_NAME_TAKEN)

    # When billing still fails after its tries, the company is removed again, so trying again
    # doesn't find its name taken.
    try:
        async with Session() as session:
            owned_ids = await companies.ids_for_user(session, user.uid)

        await billing.welcome_company(
            company.id, user.email, request.cookies.get(REFERRAL_COOKIE), owned_ids, country
        )
    except Exception:
        await delete_rows(company.id)

        raise

    await track("company_created", user_id=user.uid, company_id=company.id)

    return company


async def save(name: str, user: CurrentUser, owned: int) -> Company | None:
    """The company with its owner; refused (409) past the companies one person may own, counted
    again under a lock as it's saved. None when another company has the name, in any case."""

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

    await refuse_over(owned)
    most = await limit(get_redis(), "MAX_OWNED_COMPANIES")

    try:
        async with Session.begin() as session:
            return await companies.create(session, name, user.uid, user.email, most)
    except OverLimit as over:
        # Another company of theirs was made meanwhile: counted again under its lock.
        await refuse_over(over.count)
        raise
    except IntegrityError as error:
        if companies.name_taken(error):
            return None

        raise
