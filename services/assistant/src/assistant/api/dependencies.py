from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from testee_common.auth.auth import bearer, current_user
from testee_common.auth.service_auth import service_caller
from testee_common.auth.user import User

from assistant.config import settings
from assistant.core.security import SERVICE_NAME


def user_with_token(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
) -> tuple[User, str]:
    """The signed-in user and their raw Firebase token, which the assistant's tools send on to
    the other services as the user. The token stays in memory: never stored, logged or shown to
    the model."""
    return current_user(request, credentials), credentials.credentials


UserWithToken = Annotated[tuple[User, str], Depends(user_with_token)]

# Calls to this service (accounts deleting or exporting a user's data), signed with its own key.
ServiceCaller = service_caller(settings.service_secret, SERVICE_NAME)
