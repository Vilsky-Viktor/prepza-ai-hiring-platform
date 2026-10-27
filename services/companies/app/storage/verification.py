"""Company verification: the website, its proof by a work email, and a superadmin's review."""

from datetime import UTC, datetime

from prepza_common.events import outbox
from prepza_common.events.notifications import NOTIFICATION_REQUESTED
from sqlalchemy import case, select, update

from app.constants.verification import VerificationStatus
from app.models.companies import Company
from app.models.outbox import OutboxEvent
from app.storage.db import Session

# A new request clears the last one's decision.
UNDECIDED = {
    "decline_reason": None,
    "verification_decided_by": None,
    "verification_decided_at": None,
}


async def set_website(company_id, domain: str | None, email: str | None) -> None:
    """Saves the website's domain and takes the badge away. With `email`, the address on it
    that proves it, the company's current name goes for review; without, it waits for one. None
    clears the website and the verification with it."""
    values = {
        "website_domain": domain,
        "verified_domain": None,
        "verification_email": email,
        "verification_name": None,
        "verification_submitted_at": None,
        **UNDECIDED,
    }

    if domain is None:
        values["verification_status"] = VerificationStatus.NONE
    elif email is None:
        values["verification_status"] = VerificationStatus.WAITING_EMAIL
    else:
        values["verification_status"] = VerificationStatus.PENDING
        values["verification_name"] = Company.name
        values["verification_submitted_at"] = datetime.now(UTC)

    async with Session() as session:
        await session.execute(update(Company).where(Company.id == company_id).values(**values))
        await session.commit()


async def decide(
    company_id,
    approved: bool,
    superadmin_id: str,
    reason: str | None,
    notices: list[dict],
    seen: tuple[str, str] | None = None,
) -> bool:
    """A superadmin's decision on a pending request, with the notifications for the company's
    owners and admins. `seen` is the (name, domain) the superadmin reviewed: the request must
    still have them. False when it isn't pending any more (decided, or the website changed) or
    changed since."""
    status = VerificationStatus.APPROVED if approved else VerificationStatus.DECLINED
    conditions = [
        Company.id == company_id,
        Company.verification_status == VerificationStatus.PENDING,
    ]

    if seen is not None:
        conditions += [Company.verification_name == seen[0], Company.website_domain == seen[1]]

    async with Session() as session:
        decided = await session.scalar(
            update(Company)
            .where(*conditions)
            .values(
                verification_status=status,
                verified_domain=Company.website_domain if approved else None,
                decline_reason=None if approved else reason,
                verification_decided_by=superadmin_id,
                verification_decided_at=datetime.now(UTC),
            )
            .returning(Company.id)
        )

        if decided is not None:
            for notice in notices:
                outbox.add(session, OutboxEvent, NOTIFICATION_REQUESTED, notice)

        await session.commit()

    return decided is not None


async def requests(offset: int, limit: int) -> list[Company]:
    """Companies sent for review: the pending ones first, oldest first, then those decided,
    latest first."""
    pending = Company.verification_status == VerificationStatus.PENDING
    query = (
        select(Company)
        .where(
            Company.verification_status.in_(
                [
                    VerificationStatus.PENDING,
                    VerificationStatus.APPROVED,
                    VerificationStatus.DECLINED,
                ]
            )
        )
        .order_by(
            pending.desc(),
            case((pending, Company.verification_submitted_at)),
            Company.verification_decided_at.desc().nulls_last(),
            Company.id,
        )
        .offset(offset)
        .limit(limit)
    )

    async with Session() as session:
        return list(await session.scalars(query))
