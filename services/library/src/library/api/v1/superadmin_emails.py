import logging

from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.superadmin import SuperadminUser
from prepza_common.auth.user import UserEmailIn

from library.schemas.emails import (
    AdminEmailChangesIn,
    EmailAccountOut,
    EmailLookupOut,
    EmailPreferencesOut,
)
from library.services import email_preferences
from library.services.accounts import account_by_email, account_by_id

# The email settings of the admin zone's support tab: a superadmin stops a user's emails for someone who asked prepza
# directly. Everyone else gets "not found". Addresses go in the body, never the query string,
# which request logs record.
router = APIRouter(prefix="/superadmin/emails", tags=["superadmin"])
logger = logging.getLogger(__name__)


async def account_out(account) -> EmailAccountOut:
    return EmailAccountOut(
        user_id=account.uid,
        email=account.email,
        preferences=EmailPreferencesOut(**await email_preferences.preferences(account.uid)),
    )


@router.post("/lookup")
async def look_up(body: UserEmailIn, superadmin: SuperadminUser) -> EmailLookupOut:
    """The account signed in with the address, whatever its case, with its email settings."""
    account = await account_by_email(body.email)

    return EmailLookupOut(account=await account_out(account) if account else None)


@router.get("/accounts/{user_id}")
async def get_account(user_id: str, superadmin: SuperadminUser) -> EmailAccountOut:
    """The account with that id (the support tab's user page), with its email settings; 404
    when there's none, or it has no address to email (a company's guest candidate)."""
    account = await account_by_id(user_id)

    if account is None or not account.email:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    logger.info("Email settings of user %s viewed by superadmin %s", user_id, superadmin.uid)

    return await account_out(account)


@router.put("/{user_id}/preferences")
async def change_preferences(
    user_id: str, body: AdminEmailChangesIn, superadmin: SuperadminUser
) -> EmailPreferencesOut:
    """Changes some of the user's settings, each change logged with the admin source and the
    superadmin's id. Marketing only goes off: consent to it is the user's own. Safe to repeat: a
    setting already as asked logs nothing."""
    saved = await email_preferences.change_by_admin(user_id, body.changes, superadmin.uid)

    return EmailPreferencesOut(**saved)
