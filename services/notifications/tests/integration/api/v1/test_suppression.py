import uuid

import httpx
import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User
from prepza_common.http import http

from notifications.config import settings
from notifications.constants.bulk import SuppressionReason
from notifications.helpers.unsubscribe import address_hash
from notifications.main import app
from notifications.repositories import suppressed
from tests.integration.factories import api


def as_user(uid: str, email: str) -> None:
    app.dependency_overrides[current_user] = lambda: User(
        uid=uid, email=email, email_verified=True, sign_in_provider="google.com"
    )


def test_a_superadmin_sees_why_an_address_is_suppressed_and_takes_it_off(run, monkeypatch):
    address = f"s{uuid.uuid4().hex[:12]}@example.com"
    monkeypatch.setenv("SUPERADMIN_EMAILS", "sam@prepza.dev")

    async def scenario():
        await suppressed.add(address_hash(address), SuppressionReason.BOUNCED)
        # A later complaint keeps the first reason.
        await suppressed.add(address_hash(address), SuppressionReason.COMPLAINED)

        async with api() as client:
            as_user("ann", "ann@example.com")
            outsider = await client.post("/superadmin/suppressed/lookup", json={"email": address})
            as_user("sam", "sam@prepza.dev")
            found = (
                await client.post("/superadmin/suppressed/lookup", json={"email": address})
            ).json()
            removed = (
                await client.post("/superadmin/suppressed/remove", json={"email": address})
            ).json()
            again = await client.post("/superadmin/suppressed/remove", json={"email": address})

        app.dependency_overrides.clear()

        return outsider, found, removed, again, await suppressed.among([address_hash(address)])

    outsider, found, removed, again, left = run(scenario())

    assert outsider.status_code == 404
    assert found["reason"] == "bounced" and found["created_at"]
    assert removed == {"reason": None, "created_at": None}
    assert again.status_code == 200
    assert left == set()


@pytest.mark.parametrize("reason", list(SuppressionReason))
def test_every_reason_is_kept(run, reason):
    address = address_hash(f"r{uuid.uuid4().hex[:12]}@example.com")

    async def scenario():
        await suppressed.add(address, reason)

        return await suppressed.get(address)

    assert run(scenario()).reason == reason


@pytest.mark.parametrize(("answer", "status_code", "left"), [(200, 200, False), (401, 502, True)])
def test_taking_an_address_off_takes_it_off_resends_list_first(
    run, monkeypatch, answer, status_code, left
):
    address = f"s{uuid.uuid4().hex[:12]}@example.com"
    asked = []

    def resend(request):
        asked.append((request.method, request.url.path))

        return httpx.Response(answer, json={})

    monkeypatch.setenv("SUPERADMIN_EMAILS", "sam@prepza.dev")
    monkeypatch.setattr(settings, "resend_api_key", "re_test")
    monkeypatch.setattr(
        http, "get_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(resend))
    )

    async def scenario():
        await suppressed.add(address_hash(address), SuppressionReason.BOUNCED)

        async with api() as client:
            as_user("sam", "sam@prepza.dev")
            response = await client.post("/superadmin/suppressed/remove", json={"email": address})

        return response.status_code, await suppressed.among([address_hash(address)])

    code, found = run(scenario())

    assert asked == [("DELETE", f"/suppressions/{address}")]
    assert (code, bool(found)) == (status_code, left)
