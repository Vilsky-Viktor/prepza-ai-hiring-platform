import os

import jwt
from prepza_common.auth.user import User
from prepza_common.config.constants import KEY_ACTOR_PREFIX, KEY_SIGN_IN, VIA_MCP


def key_actor(key_id) -> str:
    """The user id an API key acts as: its own, never the member who made it."""
    return f"{KEY_ACTOR_PREFIX}{key_id}"


def actor_key(user_id: str | None) -> str | None:
    """The API key's id when `user_id` is a key acting (key_actor), None for a person."""
    if user_id and user_id.startswith(KEY_ACTOR_PREFIX):
        return user_id.removeprefix(KEY_ACTOR_PREFIX)

    return None


def key_user(token: str) -> User | None:
    """An AI agent signed in to the MCP server with an API key, as the assistant vouches for it:
    a token it signed with this service's own key (SERVICE_SECRET), issued as "mcp" with the
    key's id. Each service has its own key, so a token signed with it was made for it. None for
    any other token (a person's Firebase one)."""
    secret = os.environ.get("SERVICE_SECRET")

    if not secret:
        return None

    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"require": ["exp", "iss", "aud", "key"], "verify_aud": False},
        )
    except jwt.InvalidTokenError:
        return None

    if claims["iss"] != VIA_MCP:
        return None

    return User(
        uid=key_actor(claims["key"]),
        email="",
        email_verified=True,
        sign_in_provider=KEY_SIGN_IN,
    )
