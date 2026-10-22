from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from prepza_common import memory_cache
from prepza_common.i18n import CodedError
from prepza_common.rate_limit import hit_or_skip
from prepza_common.tokens import hashed

from app.constants.api import ACCESS_CACHE_SECONDS, LAST_USED_EVERY
from app.constants.error_codes import API_KEY_EXPIRED, INVALID_API_KEY, KEY_CREATOR_LOST_ACCESS
from app.constants.permissions import MISSING_PERMISSION, MISSING_PERMISSION_MESSAGE, Permission
from app.helpers.keys import expired
from app.integrations import companies
from app.integrations.redis import get_redis
from app.models.api import ApiKey
from app.storage import keys

bearer = HTTPBearer(auto_error=False, description="A company's API key: `Bearer pz_...`")


async def api_key(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> ApiKey:
    """The API key the request carries (checked_key)."""
    return await checked_key(credentials.credentials if credentials else None)


async def checked_key(raw: str | None) -> ApiKey:
    """The key `raw` is, counted as one request. It works until it expires, while whoever made it
    is still an owner or admin of its company, up to API_REQUESTS_PER_MINUTE requests a minute for
    the whole company (the API and the MCP server together); a 401 or 429 otherwise."""
    found = await keys.by_hash(hashed(raw)) if raw else None

    if found is None:
        raise CodedError(status.HTTP_401_UNAUTHORIZED, "Invalid API key", INVALID_API_KEY)

    now = datetime.now(UTC)

    if expired(found.expires_at, now):
        raise CodedError(status.HTTP_401_UNAUTHORIZED, "This API key has expired", API_KEY_EXPIRED)

    await limit(found.company_id)

    if not await editor(found.company_id, found.created_by):
        raise CodedError(
            status.HTTP_401_UNAUTHORIZED,
            "This key's creator is no longer an owner or admin of the company",
            KEY_CREATOR_LOST_ACCESS,
        )

    if found.last_used_at is None or now - found.last_used_at >= LAST_USED_EVERY:
        await keys.used(found.id)

    return found


async def limit(company_id: UUID) -> None:
    """Counts the request against its company. With Redis down, requests go through
    unlimited rather than all failing."""
    key = f"rate:api:{company_id}"
    await hit_or_skip(get_redis(), key, "API_REQUESTS_PER_MINUTE", company_id=company_id)


async def editor(company_id: UUID, user_id: str) -> bool:
    """Whether the key's maker is still an owner or admin, as companies said within
    ACCESS_CACHE_SECONDS."""
    key = f"api:editor:{company_id}:{user_id}"
    found = memory_cache.get(key)

    if found is None:
        found = (await companies.access(company_id, user_id))["editor"]
        memory_cache.put(key, found, ACCESS_CACHE_SECONDS)

    return found


ApiKeyDep = Annotated[ApiKey, Depends(api_key)]


class MissingPermission(Exception):
    """The key may not call the route: it doesn't have `permission`."""

    def __init__(self, permission: Permission):
        self.permission = permission


async def missing_permission(request: Request, error: MissingPermission) -> JSONResponse:
    """403 with the code `missing_permission` beside the usual `detail`, which names the
    permission."""
    message = MISSING_PERMISSION_MESSAGE.format(permission=error.permission)

    return JSONResponse(
        {"detail": message, "code": MISSING_PERMISSION}, status_code=status.HTTP_403_FORBIDDEN
    )


def needs(permission: Permission):
    """A public route's key, which must have `permission`: `key: Annotated[ApiKey, needs(...)]`.
    The API docs name it on the route (helpers/docs.py)."""

    async def permitted(key: ApiKeyDep) -> ApiKey:
        if permission not in key.permissions:
            raise MissingPermission(permission)

        return key

    permitted.permission = permission

    return Depends(permitted)
