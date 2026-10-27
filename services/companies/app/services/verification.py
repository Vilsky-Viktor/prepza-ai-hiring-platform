from prepza_common.auth.user import User

from app.constants.verification import REVIEWED, VerificationStatus
from app.helpers.verification import email_on_domain
from app.models.companies import Company
from app.storage import verification


def proves(user: User, domain: str) -> bool:
    """A verified email on the domain proves the company owns it."""
    return user.email_verified and email_on_domain(user.email, domain)


async def save_website(company: Company, user: User, domain: str) -> None:
    """Re-saving the same website keeps a verified, pending or declined company as it is,
    whoever saves it: a declined one goes for review again only after its name or website
    changes. A new website needs the saver's work email on its domain to go for review."""
    same = domain == company.website_domain

    if same and company.verification_status in REVIEWED:
        return

    email = user.email if proves(user, domain) else None

    await verification.set_website(company.id, domain, email)


async def verify_by_email(company: Company, user: User) -> None:
    """Sends a company waiting for a work email for review when this owner or admin signed in
    with one on its website's domain; the company row is updated in place."""
    domain = company.website_domain
    waiting = company.verification_status == VerificationStatus.WAITING_EMAIL

    if waiting and domain is not None and proves(user, domain):
        await verification.set_website(company.id, domain, user.email)
        company.verification_status = VerificationStatus.PENDING
