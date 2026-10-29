import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import status
from prepza_common.auth.tokens import hashed
from prepza_common.i18n.i18n import CodedError
from prepza_common.limits.rate_limit import hit_or_skip

from api.constants import error_codes
from api.constants.api import IP_NOT_ALLOWED, LAST_USED_EVERY
from api.constants.error_codes import API_KEY_EXPIRED, INVALID_API_KEY
from api.core.db import Session
from api.helpers.allowed_ips import allows
from api.helpers.keys import expired
from api.integrations.redis import get_redis
from api.models.api import ApiKey
from api.repositories import keys

logger = logging.getLogger(__name__)


async def checked_key(raw: str | None, address: str | None) -> ApiKey:
    """The key `raw` is, counted as one request from `address` (the caller's IP). It works until
    it expires, from the addresses it allows (any when it lists none), up to
    API_REQUESTS_PER_MINUTE requests a minute for the whole company (the API and the MCP server
    together); a 401, 403 or 429 otherwise. It belongs to the company: who made it doesn't
    matter, and its own permissions decide what it may do."""
    found = None

    if raw:
        async with Session() as session:
            found = await keys.by_hash(session, hashed(raw))

    if found is None:
        raise CodedError(status.HTTP_401_UNAUTHORIZED, "Invalid API key", INVALID_API_KEY)

    now = datetime.now(UTC)

    if expired(found.expires_at, now):
        raise CodedError(status.HTTP_401_UNAUTHORIZED, "This API key has expired", API_KEY_EXPIRED)

    if not allows(found.allowed_ips, address):
        logger.warning("API key %s refused: called from an address it doesn't allow", found.id)

        raise CodedError(status.HTTP_403_FORBIDDEN, IP_NOT_ALLOWED, error_codes.IP_NOT_ALLOWED)

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
