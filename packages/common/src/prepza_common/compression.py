"""Gzip for the services' answers: only the frontend sits behind Cloud CDN, which compresses its
pages, so the services' JSON reaches browsers through the load balancer as they send it."""

from fastapi import FastAPI
from starlette.middleware.gzip import GZipMiddleware

# Smaller answers gain too little to be worth the CPU and the header.
MIN_BYTES = 1_000
# zlib's default: nearly the size of level 9 for much less CPU.
LEVEL = 6


def compress_answers(app: FastAPI) -> None:
    """Gzips an answer of at least `MIN_BYTES` to a request that accepts gzip. Streams
    (`text/event-stream`: the assistant's and help chat's answers, the bell) are never
    compressed, so each event goes out as it comes: GZipMiddleware leaves that type alone."""
    app.add_middleware(GZipMiddleware, minimum_size=MIN_BYTES, compresslevel=LEVEL)
