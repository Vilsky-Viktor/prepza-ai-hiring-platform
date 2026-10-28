import asyncio
import logging

from prepza_common.config.constants import GUEST_UID_PREFIX

from library.services.accounts import delete_data, delete_sign_in

logger = logging.getLogger(__name__)


async def delete_guests(event_id: str, data: dict) -> None:
    """A deleted guest invite's guest goes too: what library kept under its sign-in (the terms
    it accepted, its ratings and reports of questions) and the sign-in itself. Safe to repeat,
    so a redelivered event changes nothing; only guests' ids are taken."""
    user_ids = data.get("user_ids")

    if not isinstance(user_ids, list):
        logger.error("Dropped malformed guests.deleted event %s", event_id)

        return

    for user_id in user_ids:
        if not isinstance(user_id, str) or not user_id.startswith(GUEST_UID_PREFIX):
            logger.error("guests.deleted event %s names a user who isn't a guest", event_id)

            continue

        await delete_data(user_id)
        await asyncio.to_thread(delete_sign_in, user_id)
