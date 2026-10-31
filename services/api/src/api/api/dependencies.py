from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from testee_common.auth.service_auth import service_caller
from testee_common.http.client_ip import client_ip

from api.config import settings
from api.constants.permissions import Permission
from api.core.exceptions import MissingPermission
from api.core.security import SERVICE_NAME
from api.models.api import ApiKey
from api.services.key_checks import checked_key

bearer = HTTPBearer(auto_error=False, description="A company's API key: `Bearer te_...`")


async def api_key(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> ApiKey:
    """The API key the request carries, from the address the load balancer saw (checked_key)."""
    return await checked_key(credentials.credentials if credentials else None, client_ip(request))


ApiKeyDep = Annotated[ApiKey, Depends(api_key)]


def needs(permission: Permission):
    """A public route's key, which must have `permission`: `key: Annotated[ApiKey, needs(...)]`.
    The API docs name it on the route (helpers/docs.py)."""

    async def permitted(key: ApiKeyDep) -> ApiKey:
        if permission not in key.permissions:
            raise MissingPermission(permission)

        return key

    permitted.permission = permission

    return Depends(permitted)


# Calls to this service, signed with its own key.
ServiceCaller = service_caller(settings.service_secret, SERVICE_NAME)
