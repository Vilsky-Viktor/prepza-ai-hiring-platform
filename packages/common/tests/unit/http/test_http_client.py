"""The shared client retries nothing: a call's one layer of retries is its caller's."""

import asyncio

import httpcore
import httpx
import pytest
from httpcore._backends import auto
from prepza_common.http import http


def test_a_failed_connection_is_tried_once(monkeypatch):
    attempts = []

    async def refused(self, host, port, **options):
        attempts.append(host)

        raise httpcore.ConnectError("refused")

    # Below httpx's own retries of a connection, which would try it again.
    monkeypatch.setattr(auto.AutoBackend, "connect_tcp", refused)
    http.get_client.cache_clear()

    async def call():
        try:
            await http.get_client().get("http://companies:8000/internal/ping")
        finally:
            await http.get_client().aclose()
            http.get_client.cache_clear()

    with pytest.raises(httpx.ConnectError):
        asyncio.run(call())

    assert attempts == ["companies"]
