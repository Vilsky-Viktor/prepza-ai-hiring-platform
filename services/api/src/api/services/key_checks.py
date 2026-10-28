from datetime import UTC, datetime
from uuid import UUID

from fastapi import status
from prepza_common.auth.tokens import hashed
from prepza_common.i18n.i18n import CodedError
from prepza_common.limits.rate_limit import hit_or_skip
from prepza_common.redis import memory_cache

from api.constants.api import ACCESS_CACHE_SECONDS, LAST_USED_EVERY
from api.constants.error_codes import API_KEY_EXPIRED, INVALID_API_KEY, KEY_CREATOR_LOST_ACCESS
from api.core.db import Session
from api.helpers.keys import expired
from api.integrations import companies
from api.integrations.redis import get_redis
from api.models.api import ApiKey
from api.repositories import keys


async def checked_key(raw: str | None) -> ApiKey:
    """The key `raw` is, counted as one request. It works until it expires, while whoever made it
    is still an owner or admin of its company, up to API_REQUESTS_PER_MINUTE requests a minute for
    the whole company (the API and the MCP server together); a 401 or 429 otherwise."""
    found = None

    if raw:
        async with Session() as session:
            found = await keys.by_hash(session, hashed(raw))

    if found is None:
        raise CodedError(status.HTTP_401_UNAUTHORIZED, "Invalid API key", INVALID_API_KEY)

    now = datetime.now(UTC)

    if expired(found.expires_at, now):
        raise CodedError(status.HTTP_401_UNAUTHORIZED, "This API key has expired", API_KEY_EXPIRED)

    if not await editor(found.company_id, found.created_by):
        raise CodedError(
            status.HTTP_401_UNAUTHORIZED,
            "This key's creator is no longer an owner or admin of the company",
            KEY_CREATOR_LOST_ACCESS,
        )

    # Counted once the key works: a refused one doesn't use up its company's requests.
    await limit(found.company_id)

    if found.last_used_at is None or now - found.last_used_at >= LAST_USED_EVERY:
        async with Session.begin() as session:
            await keys.used(session, found.id)

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
