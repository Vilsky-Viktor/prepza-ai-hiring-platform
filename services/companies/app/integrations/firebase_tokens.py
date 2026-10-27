import asyncio
from uuid import UUID

from firebase_admin import auth as firebase_auth
from prepza_common.config.constants import GUEST_UID_PREFIX


def guest_uid(invite_id: UUID) -> str:
    return f"{GUEST_UID_PREFIX}{invite_id}"


async def guest_token(invite_id: UUID) -> str:
    """A custom token that signs the browser in as the invite's guest; Firebase makes the account
    on its first sign-in."""
    token = await asyncio.to_thread(firebase_auth.create_custom_token, guest_uid(invite_id))

    return token.decode()
