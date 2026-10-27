import asyncio

from firebase_admin import auth as firebase_auth
from firebase_admin.exceptions import ResourceExhaustedError
from prepza_common.auth.auth import verify
from prepza_common.auth.user import User
from prepza_common.http import http
from prepza_common.limits.limits import record_hit
from prepza_common.redis import memory_cache

from app.config.settings import settings
from app.constants.mcp import (
    EXPIRY_MARGIN_SECONDS,
    FIREBASE_LIMIT_ERRORS,
    ID_TOKEN_CACHE_KEY,
    IDENTITY_TOOLKIT,
    MAX_KEEP_SECONDS,
)


async def refused_for_limits(response, user_id: str) -> None:
    """Records Firebase refusing a sign-in for its own limits (a 429, too many attempts, a
    quota), not for a bad token."""
    try:
        message = response.json().get("error", {}).get("message", "")
    except ValueError:
        message = ""

    if response.status_code == 429 or message.startswith(FIREBASE_LIMIT_ERRORS):
        await record_hit("FIREBASE_TOKEN_REFUSED", kind="provider:firebase", user_id=user_id)


def identity_url() -> str:
    """Firebase's sign-in API: the Auth emulator's locally."""
    if settings.firebase_auth_emulator_host:
        return f"http://{settings.firebase_auth_emulator_host}/identitytoolkit.googleapis.com/v1"

    return IDENTITY_TOOLKIT


async def sign_in(uid: str) -> tuple[User, str] | None:
    """The user and a Firebase ID token of theirs, as if they had signed in: an AI app's calls
    go to the other services with it, which check it as any user's. Kept in memory for at most
    MAX_KEEP_SECONDS. None when the account is gone or disabled; never for an unknown uid (a
    custom token would create that user)."""
    cached = memory_cache.get(ID_TOKEN_CACHE_KEY.format(uid=uid))

    if cached is not None:
        return cached

    try:
        account = await asyncio.to_thread(firebase_auth.get_user, uid)
    except firebase_auth.UserNotFoundError:
        return None
    except ResourceExhaustedError:
        await record_hit("FIREBASE_TOKEN_REFUSED", kind="provider:firebase", user_id=uid)

        raise

    if account.disabled:
        return None

    custom = await asyncio.to_thread(firebase_auth.create_custom_token, uid)
    response = await http.get_client().post(
        f"{identity_url()}/accounts:signInWithCustomToken",
        params={"key": settings.firebase_web_api_key},
        json={"token": custom.decode(), "returnSecureToken": True},
    )

    if response.is_error:
        await refused_for_limits(response, uid)

    response.raise_for_status()
    found = response.json()
    # The check may fetch Google's certificates, a blocking call.
    user = await asyncio.to_thread(verify, found["idToken"])

    if user is None:
        return None

    seconds = min(int(found["expiresIn"]) - EXPIRY_MARGIN_SECONDS, MAX_KEEP_SECONDS)
    memory_cache.put(ID_TOKEN_CACHE_KEY.format(uid=uid), (user, found["idToken"]), seconds)

    return user, found["idToken"]


def forget(uid: str) -> None:
    """Drops the user's kept token, so the next call signs in again (their language changed)."""
    memory_cache.put(ID_TOKEN_CACHE_KEY.format(uid=uid), None, 0)
