import asyncio
from typing import Literal

from fastapi import APIRouter
from prepza_common.db.paging import IdPageParams

from library.api.dependencies import ServiceCaller
from library.constants.emails import ConsentSource, EmailSetting
from library.core.db import Session
from library.repositories import emails
from library.schemas.emails import (
    EmailPreferencesOut,
    RecipientsIn,
    RecipientsOut,
    UnsubscribeIn,
    UserIdsOut,
    WithSettingIn,
)
from library.services import email_preferences
from library.services.email_recipients import recipients, user_ids_after

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
        async with Session() as session:
            found = await emails.ids_with(session, EmailSetting(setting), page.after, page.limit)

        return UserIdsOut(user_ids=found)

    return UserIdsOut(user_ids=await asyncio.to_thread(user_ids_after, page.after, page.limit))


@router.post("/with-setting")
async def users_with_setting(body: WithSettingIn, caller: ServiceCaller) -> UserIdsOut:
    """Notifications, for a campaign to some groups (companies, candidates, learners): those of
    the users who have its setting on."""
    async with Session() as session:
        return UserIdsOut(user_ids=await emails.having(session, body.setting, body.user_ids))


@router.post("/{user_id}/unsubscribe")
async def unsubscribe(
    user_id: str, body: UnsubscribeIn, caller: ServiceCaller
) -> EmailPreferencesOut:
    """Notifications, for an email's unsubscribe link (checked there): turns the settings off,
    logged as an unsubscribe. Safe to repeat: a setting already off logs nothing."""
    changes = dict.fromkeys(body.settings, False)

    saved = await email_preferences.change(user_id, changes, ConsentSource.UNSUBSCRIBE)

    return EmailPreferencesOut(**saved)


@router.post("/email-recipients")
async def email_recipients(body: RecipientsIn, caller: ServiceCaller) -> RecipientsOut:
    """Notifications, for its emails to many users at once (the activity digest, reminders): each
    user's address, interface language and preferences; users who are gone are left out."""
    return RecipientsOut(recipients=await recipients(body.user_ids))
