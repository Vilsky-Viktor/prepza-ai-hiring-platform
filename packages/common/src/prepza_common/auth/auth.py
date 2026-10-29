from typing import Annotated

import firebase_admin
import sentry_sdk
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth
from firebase_admin.exceptions import FirebaseError
from prepza_common.auth.key_actor import key_user
from prepza_common.auth.user import User
from prepza_common.config.constants import (
    DEFAULT_LANGUAGE,
    GOOGLE_TIMEOUT_SECONDS,
    KEY_SIGN_IN,
    LANGUAGE_CLAIM,
    LANGUAGES,
    READ_METHODS,
    SIGN_IN_UNAVAILABLE,
    SUPERADMIN_PREFIX,
)

bearer = HTTPBearer()
optional_bearer = HTTPBearer(auto_error=False)


def start_firebase(project_id: str) -> None:
    """Firebase Admin for a service's lifespan; each of its calls gives up after
    GOOGLE_TIMEOUT_SECONDS."""
    firebase_admin.initialize_app(
        options={"projectId": project_id, "httpTimeout": GOOGLE_TIMEOUT_SECONDS}
    )


def verify(token: str, check_revoked: bool = False) -> User | None:
    """The user a Firebase ID token belongs to, or None when it isn't valid. With
    `check_revoked`, Firebase is also asked whether the account still exists and its sign-ins
    weren't revoked (account deletion revokes them), which a valid token alone can't say for up
    to an hour.

    When Google's signing certificates (or, checking revocation, Firebase) can't be reached, no
    token can be checked: that's our outage, not a bad token, so it's a 503 rather than a 401.
    """
    try:
        claims = firebase_auth.verify_id_token(token, check_revoked=check_revoked)
    except (
        ValueError,
        firebase_auth.InvalidIdTokenError,
        firebase_auth.UserDisabledError,
        firebase_auth.UserNotFoundError,
    ):
        return None
    except FirebaseError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, SIGN_IN_UNAVAILABLE)

    return User(
        uid=claims["uid"],
        email=claims.get("email", ""),
        email_verified=claims.get("email_verified", False),
        name=claims.get("name"),
        language=claims_language(claims),
        sign_in_provider=claims.get("firebase", {}).get("sign_in_provider"),
    )


def claims_language(claims: dict) -> str:
    """The interface language a user's sign-in claims hold (the default when none is set)."""
    language = claims.get(LANGUAGE_CLAIM)

    return language if language in LANGUAGES else DEFAULT_LANGUAGE


def writes(request: Request) -> bool:
    """Whether the request may change something: its token is then checked for revocation."""
    return request.method not in READ_METHODS


def signed_in(request: Request, token: str) -> User | None:
    """A person's Firebase token (checked for revocation when the request writes), or an API
    key's token from the assistant (key_user); None for anything else."""
    return verify(token, check_revoked=writes(request)) or key_user(token)


def current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(optional_bearer)],
) -> User:
    """The signed-in user; 401 without a valid token, except on the admin zone's routes, which
    answer 404 to everyone else, signed out included, so they don't show they exist. An AI
    agent signed in with an API key is the key (key_actor)."""
    user = signed_in(request, credentials.credentials) if credentials else None

    if user is None:
        if request.scope.get("path", "").startswith(SUPERADMIN_PREFIX):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    # Errors from this request name the account by id only, never by email.
    sentry_sdk.set_user({"id": user.uid})

    return user


def optional_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(optional_bearer)],
) -> User | None:
    """The signed-in user, or None for anonymous visitors and stale tokens on public pages."""
    if credentials is None:
        return None

    return signed_in(request, credentials.credentials)


def fresh_user(
    request: Request,
    user: Annotated[User, Depends(current_user)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(optional_bearer)],
) -> User:
    """The signed-in user, refused (401) once their sign-in was revoked (a deleted account, a
    signed-out session) even for a read: for reads that hand over a lot of personal data (a
    data export, the admin zone, a long-lived stream). A write's token was checked already."""
    revocable = (
        credentials is not None and not writes(request) and user.sign_in_provider != KEY_SIGN_IN
    )

    if revocable and verify(credentials.credentials, check_revoked=True) is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    return user


CurrentUser = Annotated[User, Depends(current_user)]
FreshUser = Annotated[User, Depends(fresh_user)]
OptionalUser = Annotated[User | None, Depends(optional_user)]
