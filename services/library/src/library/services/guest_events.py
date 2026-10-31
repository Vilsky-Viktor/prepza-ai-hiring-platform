import logging

from testee_common.config.constants import GUEST_UID_PREFIX

from library.services.user_data import delete_data

logger = logging.getLogger(__name__)


async def delete_guests(event_id: str, data: dict) -> None:
    """A deleted guest invite's guest goes too: what library kept under its sign-in (its ratings
    and reports of questions; accounts deletes the sign-in on the same event). Safe to repeat,
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
