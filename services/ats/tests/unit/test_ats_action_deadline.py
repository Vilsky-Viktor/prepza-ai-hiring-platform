"""One action of an ATS's client ends within ATS_ACTION_SECONDS, however many pages it reads."""

import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.ats import AtsConnection
from app.services import ats as ats_service


def test_an_ats_that_takes_too_long_over_its_pages_didnt_answer(monkeypatch):
    async def pages_forever(token):
        await asyncio.Event().wait()

    slow = SimpleNamespace(
        KEYS=("token",), UNAVAILABLE="Slow ATS didn't answer", jobs=pages_forever
    )

    async def credentials(connection):
        return {"token": "t"}

    monkeypatch.setattr(ats_service, "credentials", credentials)
    monkeypatch.setattr(ats_service, "client", lambda provider: slow)
    monkeypatch.setattr(ats_service, "ATS_ACTION_SECONDS", 0.01)
    connection = AtsConnection(provider="workable", status="connected")

    with pytest.raises(HTTPException) as refused:
        asyncio.run(ats_service.jobs(connection))

    assert (refused.value.status_code, refused.value.detail) == (502, "Slow ATS didn't answer")
