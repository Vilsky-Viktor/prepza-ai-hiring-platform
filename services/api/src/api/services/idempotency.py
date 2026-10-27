import hashlib
import json
import logging
from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import status
from prepza_common.i18n.i18n import CodedError
from redis.exceptions import RedisError

from api.constants import error_codes
from api.constants.api import (
    IDEMPOTENCY_IN_PROGRESS,
    IDEMPOTENCY_KEY_REUSED,
    IDEMPOTENCY_SECONDS,
    RETRY_WINDOW_SECONDS,
)
from api.integrations.redis import get_redis

logger = logging.getLogger(__name__)
PENDING = "pending"


def fingerprint(*parts: object) -> str:
    """A request's identity: what it acts on and its body, as canonical JSON, hashed."""
    canonical = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str)

    return hashlib.sha256(canonical.encode()).hexdigest()


def slot(company_id: UUID, key_id: UUID, client_key: str | None, request: str) -> tuple[str, int]:
    """Where a create's first result is kept, and for how long. With the client's
    `Idempotency-Key` (still taken from integrations that send one): that key, a day. Without
    one, derived here from the API key and the request itself, for RETRY_WINDOW_SECONDS: a
    network retry gets the first result, while the same request made on purpose later creates
    again. Clients never need to send a key."""
    if client_key:
        digest = hashlib.sha256(client_key.encode()).hexdigest()

        return f"api:idempotency:{company_id}:{digest}", IDEMPOTENCY_SECONDS

    return f"api:idempotency:derived:{key_id}:{request}", RETRY_WINDOW_SECONDS


async def once(name: str, seconds: int, request: str, run: Callable[[], Awaitable[str]]) -> str:
    """Runs `run` once for `name` within `seconds`: a retry gets the first run's result (an id)
    without running it again; one while the first still runs is refused (409); the same client
    key with another request (`request`, its fingerprint) is refused (422). A run that fails
    frees the name. With Redis down, it just runs."""
    redis = get_redis()

    try:
        claimed = await redis.set(name, f"{request}:{PENDING}", nx=True, ex=seconds)
        stored = None if claimed else await redis.get(name)
        earlier = stored.decode() if stored is not None else None
    except RedisError as error:
        logger.warning("Idempotency skipped, Redis failed: %s", error)

        return await run()

    if earlier is not None:
        # Kept before requests were fingerprinted: the result alone.
        made_by, _, result = earlier.rpartition(":")

        if made_by and made_by != request:
            raise CodedError(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                IDEMPOTENCY_KEY_REUSED,
                error_codes.IDEMPOTENCY_KEY_REUSED,
            )

        if result == PENDING:
            raise CodedError(
                status.HTTP_409_CONFLICT, IDEMPOTENCY_IN_PROGRESS, error_codes.REQUEST_IN_PROGRESS
            )

        return result

    try:
        result = await run()
    except Exception:
        await _forget(name)

        raise

    try:
        await redis.set(name, f"{request}:{result}", ex=seconds)
    except RedisError as error:
        # Made all the same, so it's answered; until the claim expires, a retry is told the first
        # still runs (409) rather than making it twice.
        logger.warning("Idempotency result not kept, Redis failed: %s", error)

    return result


async def _forget(name: str) -> None:
    """Frees a failed run's claim, so a retry runs again; with Redis down, it expires instead
    and the run's own error is what the client gets."""
    try:
        await get_redis().delete(name)
    except RedisError as error:
        logger.warning("Idempotency claim not freed, Redis failed: %s", error)
