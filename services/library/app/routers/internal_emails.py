import asyncio
from typing import Literal

from fastapi import APIRouter
from prepza_common.paging import IdPageParams

from app.constants.emails import ConsentSource, EmailSetting
from app.schemas.emails import (
    EmailPreferencesOut,
    RecipientsIn,
    RecipientsOut,
    UnsubscribeIn,
    UserIdsOut,
)
from app.service_auth import ServiceCaller
from app.services.email_recipients import recipients, user_ids_after
from app.storage import emails

router = APIRouter(prefix="/internal/users", tags=["internal"])


@router.get("/ids")
async def user_ids(
    caller: ServiceCaller,
    page: IdPageParams,
    setting: Literal["updates", "promotions"] | None = None,
) -> UserIdsOut:
    """Notifications, a page at a time: every account, for a notice about the terms or the
    privacy policy; with a `setting`, the users who have it on (a campaign's product updates or
    offers)."""
    if setting is not None:
        found = await emails.ids_with(EmailSetting(setting), page.after, page.limit)

        return UserIdsOut(user_ids=found)

    return UserIdsOut(user_ids=await asyncio.to_thread(user_ids_after, page.after, page.limit))


@router.post("/{user_id}/unsubscribe")
async def unsubscribe(
    user_id: str, body: UnsubscribeIn, caller: ServiceCaller
) -> EmailPreferencesOut:
    """Notifications, for an email's unsubscribe link (checked there): turns the settings off,
    logged as an unsubscribe. Safe to repeat: a setting already off logs nothing."""
    changes = dict.fromkeys(body.settings, False)

    return EmailPreferencesOut(**await emails.change(user_id, changes, ConsentSource.UNSUBSCRIBE))


@router.post("/email-recipients")
async def email_recipients(body: RecipientsIn, caller: ServiceCaller) -> RecipientsOut:
    """Notifications, for its emails to many users at once (the activity digest, reminders): each
    user's address, interface language and preferences; users who are gone are left out."""
    return RecipientsOut(recipients=await recipients(body.user_ids))
