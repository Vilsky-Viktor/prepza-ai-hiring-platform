"""Inviting each address of a list, one by one as a single invite would (routers/bulk_invites.py)."""

import logging

from fastapi import HTTPException, status
from prepza_common.user import User

from app.constants.invites import SKIP_REASONS, STARTED, SkipReason
from app.models.companies import Company
from app.models.interviews import Interview
from app.schemas.invites import SkippedInvite
from app.services import candidate_invites
from app.storage import invites

logger = logging.getLogger(__name__)


async def invite_each(
    interview: Interview, company: Company, user: User, found: list[tuple[str, str | None]]
) -> tuple[list[str], list[SkippedInvite]]:
    """(invited emails, skipped ones with why). Once credits run out, the rest are skipped."""
    invited: list[str] = []
    skipped: list[SkippedInvite] = []
    out_of_credits = False
    # Looked up at once: an invite the list starts below isn't started either.
    statuses = await invites.statuses_of(interview.id, [email.lower() for email, _ in found])

    for email, name in found:
        reason = None

        if out_of_credits:
            reason = SkipReason.NO_CREDITS
        elif statuses.get(email.lower()) in STARTED:
            reason = SkipReason.STARTED
        else:
            try:
                await candidate_invites.invite(interview, company, user, email, name)
            except HTTPException as error:
                out_of_credits = error.status_code == status.HTTP_402_PAYMENT_REQUIRED
                reason = SKIP_REASONS.get(error.status_code, SkipReason.FAILED)
            except Exception:
                logger.exception("Couldn't invite a candidate from a list")
                reason = SkipReason.FAILED

        if reason:
            skipped.append(SkippedInvite(email=email, reason=reason))
        else:
            invited.append(email)

    return invited, skipped
