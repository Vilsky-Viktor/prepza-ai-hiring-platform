import os
from datetime import UTC, datetime
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from prepza_common.constants import NOT_ALLOWED, SERVICE_TOKEN_LIFETIME

bearer = HTTPBearer()


def callee_secret(callee: str) -> str:
    """The key of the service being called: each service has its own, and a caller holds only
    the keys of services it calls (<CALLEE>_SERVICE_SECRET, e.g. LIBRARY_SERVICE_SECRET)."""
    return os.environ[f"{callee.upper()}_SERVICE_SECRET"]


def issue_token(caller: str, callee: str, secret: str, extra: dict | None = None) -> str:
    """A short-lived token from `caller`, usable only at `callee`, signed with `callee`'s key;
    `extra` claims ride along, signed too."""
    now = datetime.now(UTC)
    claims = {
        **(extra or {}),
        "iss": caller,
        "aud": callee,
        "iat": now,
        "exp": now + SERVICE_TOKEN_LIFETIME,
    }

    return jwt.encode(claims, secret, algorithm="HS256")


def token_claims(token: str, secret: str, name: str) -> dict | None:
    """The claims of `token` when it's addressed to service `name`, signed with its key and not
    expired; None otherwise."""
    try:
        return jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience=name,
            options={"require": ["exp", "iss", "aud"]},
        )
    except jwt.InvalidTokenError:
        return None


def token_caller(token: str, secret: str, name: str) -> str | None:
    """The calling service's name when `token` is addressed to service `name`, signed with its
    key and not expired; None otherwise."""
    claims = token_claims(token, secret, name)

    return claims["iss"] if claims else None


def service_caller(secret: str, name: str):
    """A FastAPI parameter type that admits only tokens addressed to service `name` and signed
    with its key; it holds the calling service's name."""

    def verify_service(
        credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    ) -> str:
        caller = token_caller(credentials.credentials, secret, name)

        if caller is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid service token")

        return caller

    return Annotated[str, Depends(verify_service)]


def only_from(caller: str, allowed: str) -> None:
    """Refuses a call from any service but `allowed`, for an internal route only it may use."""
    if caller != allowed:
        raise HTTPException(status.HTTP_403_FORBIDDEN, NOT_ALLOWED)
