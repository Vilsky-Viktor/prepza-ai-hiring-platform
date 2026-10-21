"""Accounts deleted in the backups' life are deleted again everywhere, so a restore brings
nobody back (services/erasures.py)."""

import asyncio
from types import SimpleNamespace

import httpx
import pytest

from app.integrations import accounts as services
from app.services import erasures as replays
from app.storage import accounts, erasures


@pytest.fixture
def done(monkeypatch):
    calls = []

    async def since(after):
        calls.append(("since", after.tzinfo is not None))

        return [SimpleNamespace(user_id="u1", email="ann@example.com")]

    async def forget(before):
        calls.append("forget")

    async def delete_user(service, user_id, email):
        calls.append((service, user_id, email))

    async def delete_library(user_id):
        calls.append(("library", user_id))

    monkeypatch.setattr(erasures, "since", since)
    monkeypatch.setattr(erasures, "forget", forget)
    monkeypatch.setattr(services, "delete_user", delete_user)
    monkeypatch.setattr(accounts, "delete_user", delete_library)

    return calls


def test_every_recent_erasure_is_run_again_in_every_service_after_older_ones_go(done):
    assert asyncio.run(replays.replay()) == 1

    assert done[:2] == ["forget", ("since", True)]
    assert done[2:] == [
        *[(service, "u1", "ann@example.com") for service in services.services()],
        ("library", "u1"),
    ]


def test_a_service_refusing_a_shared_company_doesnt_stop_the_others(done, monkeypatch):
    async def refuse(service, user_id, email):
        if service == "companies":
            response = httpx.Response(409, request=httpx.Request("DELETE", "http://companies"))
            raise httpx.HTTPStatusError("refused", request=response.request, response=response)

        done.append(service)

    monkeypatch.setattr(services, "delete_user", refuse)

    assert asyncio.run(replays.replay()) == 1
    assert "rounds" in done and ("library", "u1") in done
