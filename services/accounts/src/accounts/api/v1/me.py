from fastapi import APIRouter, status
from prepza_common.auth.auth import CurrentUser
from prepza_common.http.visitor_country import VisitorCountry

from accounts.schemas.emails import EmailPreferencesIn, EmailPreferencesOut
from accounts.schemas.me import SettingsIn
from accounts.services import email_preferences
from accounts.services.accounts import set_language

# Public at /api/accounts/ and, as before, at /api/library/me/... (gateway/nginx.conf and the
# load balancer's account_paths send those to this service).
router = APIRouter()


@router.put("/me/settings", status_code=status.HTTP_204_NO_CONTENT)
async def update_settings(
    body: SettingsIn, user: CurrentUser, country: VisitorCountry = None
) -> None:
    """Takes effect once the frontend refreshes the user's ID token."""
    await set_language(user, body.language, country)


@router.get("/me/email-preferences")
async def get_email_preferences(user: CurrentUser) -> EmailPreferencesOut:
    return EmailPreferencesOut(**await email_preferences.preferences(user.uid))


@router.put("/me/email-preferences")
async def update_email_preferences(
    body: EmailPreferencesIn, user: CurrentUser
) -> EmailPreferencesOut:
    """Changes some settings; each change is logged as consent given or withdrawn."""
    saved = await email_preferences.change(user.uid, body.changes, body.source)

    return EmailPreferencesOut(**saved)
