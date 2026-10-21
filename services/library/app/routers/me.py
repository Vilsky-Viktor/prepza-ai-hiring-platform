from fastapi import APIRouter, Response, status
from fastapi.encoders import jsonable_encoder
from prepza_common.auth import CurrentUser, FreshUser
from prepza_common.rate_limit import hit_or_skip
from prepza_common.superadmin import is_superadmin
from prepza_common.visitor_country import VisitorCountry

from app.integrations.redis import get_redis
from app.schemas.emails import EmailPreferencesIn, EmailPreferencesOut
from app.schemas.me import MeOut, SettingsIn
from app.services.accounts import delete_account, export_account, set_language
from app.storage import emails

router = APIRouter()


@router.get("/me")
def me(user: CurrentUser) -> MeOut:
    return MeOut(**user.model_dump(), is_superadmin=is_superadmin(user))


@router.put("/me/settings", status_code=status.HTTP_204_NO_CONTENT)
async def update_settings(
    body: SettingsIn, user: CurrentUser, country: VisitorCountry = None
) -> None:
    """Takes effect once the frontend refreshes the user's ID token."""
    await set_language(user, body.language, country)


@router.get("/me/email-preferences")
async def get_email_preferences(user: CurrentUser) -> EmailPreferencesOut:
    return EmailPreferencesOut(**await emails.preferences(user.uid))


@router.put("/me/email-preferences")
async def update_email_preferences(
    body: EmailPreferencesIn, user: CurrentUser
) -> EmailPreferencesOut:
    """Changes some settings; each change is logged as consent given or withdrawn."""
    return EmailPreferencesOut(**await emails.change(user.uid, body.changes, body.source))


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(user: CurrentUser) -> None:
    """Deletes the account and everything about it. A company the user alone owns goes too."""
    await delete_account(user)


@router.get("/me/export")
async def export_me(user: FreshUser, response: Response) -> dict:
    """Everything prepza holds about the user, as one JSON file to download."""
    # Each export asks every service for the account's data.
    key = f"rate:data-exports:{user.uid}"
    await hit_or_skip(get_redis(), key, "DATA_EXPORTS_PER_HOUR", user_id=user.uid)
    response.headers["Content-Disposition"] = 'attachment; filename="prepza-data.json"'

    return jsonable_encoder(await export_account(user))
