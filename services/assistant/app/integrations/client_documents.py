import asyncio
import json
import logging
import socket
from functools import cache

import httpx
from prepza_common.http.public_urls import pinned, resolved_address

from app.constants.limits import MAX_REGISTRATION_BYTES
from app.constants.mcp import METADATA_DOCUMENT_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


@cache
def get_client() -> httpx.AsyncClient:
    """Its own client, keeping no connections: one opened for a host would otherwise be reused
    for another host at the same address, without checking that host's certificate."""
    return httpx.AsyncClient(limits=httpx.Limits(max_keepalive_connections=0))


async def read(url: str) -> dict | None:
    """An AI app's Client ID Metadata Document, as JSON, from its HTTPS address on the public
    internet, connected to the address that was checked, without following redirects, within
    METADATA_DOCUMENT_TIMEOUT_SECONDS and MAX_REGISTRATION_BYTES. None when it can't be read."""
    try:
        address = await resolved_address(url)
    except socket.gaierror:
        return None

    if address is None:
        logger.info("An AI app's metadata document isn't on a public HTTPS address")

        return None

    target, host, extensions = pinned(url, address)
    body = b""

    try:
        async with asyncio.timeout(METADATA_DOCUMENT_TIMEOUT_SECONDS):
            async with get_client().stream(
                "GET",
                target,
                headers={**host, "Accept": "application/json"},
                extensions=extensions,
            ) as response:
                if response.status_code != httpx.codes.OK:
                    return None

                async for chunk in response.aiter_bytes():
                    body += chunk

                    if len(body) > MAX_REGISTRATION_BYTES:
                        return None
    except (TimeoutError, httpx.HTTPError):
        return None

    try:
        found = json.loads(body)
    except ValueError:
        return None

    return found if isinstance(found, dict) else None
