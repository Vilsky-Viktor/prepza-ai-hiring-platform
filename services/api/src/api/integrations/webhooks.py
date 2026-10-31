import asyncio
from functools import cache

import httpx
from testee_common.http.public_urls import pinned

from api.constants.api import SIGNATURE_HEADER, WEBHOOK_TIMEOUT_SECONDS


@cache
def get_client() -> httpx.AsyncClient:
    """Web hooks' own client, keeping no connections: one opened for a host would otherwise be
    reused for another host at the same address, without checking that host's certificate."""
    return httpx.AsyncClient(limits=httpx.Limits(max_keepalive_connections=0))


async def post(url: str, address: str, body: bytes, signature: str) -> None:
    """Sends an event to a company's endpoint at `address`, the one its host was checked to have
    (see public_address), with the host's name in the Host header and TLS (SNI and the
    certificate check), without following redirects; anything but a 2xx answer raises an
    httpx.HTTPError.

    Only the answer's status is read, never its body, and the whole send has one time limit: an
    endpoint that answers gigabytes, or a byte at a time, can't hold the service.
    """
    target, host, extensions = pinned(url, address)

    try:
        async with asyncio.timeout(WEBHOOK_TIMEOUT_SECONDS):
            async with get_client().stream(
                "POST",
                target,
                content=body,
                headers={**host, "Content-Type": "application/json", SIGNATURE_HEADER: signature},
                extensions=extensions,
                timeout=WEBHOOK_TIMEOUT_SECONDS,
            ) as response:
                response.raise_for_status()
    except TimeoutError:
        raise httpx.TimeoutException("The web hook's endpoint took too long") from None
