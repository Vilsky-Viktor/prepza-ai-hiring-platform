"""A service's end: what it holds open, closed at the end of its lifespan. Cloud Run kills the
container 10 seconds after asking it to stop, and uvicorn ends the requests still running after
--timeout-graceful-shutdown (8 s) first, so this runs in the time left."""

import logging

from sqlalchemy.ext.asyncio import AsyncEngine
from testee_common.http import http

logger = logging.getLogger(__name__)


async def close_shared(engine: AsyncEngine, redis, *clients) -> None:
    """Closes the shared HTTP client and the service's own `clients` (anything with `aclose`),
    Redis, and the database pool, whose connections go back to Postgres at once rather than
    counting against its connection budget until Postgres notices them gone. One that fails to
    close doesn't keep the rest open."""
    closes = [http.get_client().aclose, *(client.aclose for client in clients), redis.aclose]

    for close in [*closes, engine.dispose]:
        try:
            await close()
        except Exception:
            logger.warning("Couldn't close a connection at shutdown", exc_info=True)
