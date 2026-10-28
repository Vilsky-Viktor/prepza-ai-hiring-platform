from fastapi import HTTPException, status
from prepza_common.auth.user import User
from prepza_common.events.audit_actions import AuditAction, TargetKind

from companies.constants.verification import (
    FREE_DOMAIN,
    NOT_A_WEBSITE,
    REVIEWED,
    VerificationStatus,
)
from companies.core.db import Session
from companies.helpers.verification import email_on_domain, is_free_domain, website_domain
from companies.models.companies import Company
from companies.repositories import audit, companies, verification


def proves(user: User, domain: str) -> bool:
    """A verified email on the domain proves the company owns it."""
    return user.email_verified and email_on_domain(user.email, domain)


async def change_website(company: Company, user: User, website: str) -> Company:
    """Saves the company's website, or clears it (and its verification) when blank; a new one
    is recorded in the action log in the same save. Refuses (422) an address that isn't a
    website or a free mail service's. Returns the company as saved."""
    if not website.strip():
        async with Session.begin() as session:
            await verification.set_website(session, company.id, None, None)
    else:
        domain = website_domain(website)

        if domain is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, NOT_A_WEBSITE)

        if is_free_domain(domain):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, FREE_DOMAIN)

        async with Session.begin() as session:
            await save_website(session, company, user, domain)
            await audit.record(
                session,
                company.id,
                user.uid,
                AuditAction.VERIFICATION_REQUESTED,
                company.id,
                target_kind=TargetKind.COMPANY,
                target_label=domain,
            )

    async with Session() as session:
        return await companies.get(session, company.id)


async def save_website(session, company: Company, user: User, domain: str) -> None:
    """Re-saving the same website keeps a verified, pending or declined company as it is,
    whoever saves it: a declined one goes for review again only after its name or website
    changes. A new website needs the saver's work email on its domain to go for review."""
    same = domain == company.website_domain

    if same and company.verification_status in REVIEWED:
        return

    email = user.email if proves(user, domain) else None

    await verification.set_website(session, company.id, domain, email)


async def verify_by_email(company: Company, user: User) -> None:
    """Sends a company waiting for a work email for review when this owner or admin signed in
    with one on its website's domain; the company row is updated in place."""
    domain = company.website_domain
    waiting = company.verification_status == VerificationStatus.WAITING_EMAIL

    if waiting and domain is not None and proves(user, domain):
        async with Session.begin() as session:
            await verification.set_website(session, company.id, domain, user.email)

        company.verification_status = VerificationStatus.PENDING
