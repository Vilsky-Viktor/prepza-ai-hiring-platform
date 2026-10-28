import logging

from fastapi import HTTPException, status

from accounts.constants.emails import (
    ADMIN_CANT_CONSENT,
    MARKETING_SETTINGS,
    ConsentSource,
    EmailSetting,
)
from accounts.core.db import Session
from accounts.helpers.emails import consent_changes
from accounts.repositories import emails
from accounts.services.accounts import account_by_id

logger = logging.getLogger(__name__)


async def preferences(user_id: str) -> dict[str, bool]:
    async with Session() as session:
        return await emails.preferences(session, user_id)


async def change(
    user_id: str,
    changes: dict[EmailSetting, bool],
    source: ConsentSource,
    changed_by: str | None = None,
) -> dict[str, bool]:
    """Applies the changes and logs each one that changes something (consent_changes), so a
    repeated request logs nothing twice; the preferences as they now are. `changed_by` is the
    superadmin, for the admin source."""
    async with Session.begin() as session:
        row, new = await emails.lock(session, user_id)
        applied = consent_changes(emails.as_dict(row), changes, source, new)

        return emails.apply(session, row, applied, source, changed_by)


async def change_by_admin(
    user_id: str, changes: dict[EmailSetting, bool], superadmin_id: str
) -> dict[str, bool]:
    """A superadmin's change, logged with the admin source and their id. Marketing only goes
    off: consent to it is the user's own. 404 when there's no such account."""
    if any(on and setting in MARKETING_SETTINGS for setting, on in changes.items()):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, ADMIN_CANT_CONSENT)

    if await account_by_id(user_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    saved = await change(user_id, changes, ConsentSource.ADMIN, superadmin_id)
    logger.warning(
        "Email settings of user %s changed by superadmin %s: %s",
        user_id,
        superadmin_id,
        {setting.value: on for setting, on in changes.items()},
    )

    return saved
