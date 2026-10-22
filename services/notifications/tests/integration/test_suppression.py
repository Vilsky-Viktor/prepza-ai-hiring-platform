import uuid

import pytest
from prepza_common.auth import current_user
from prepza_common.user import User

from app.constants.bulk import SuppressionReason
from app.helpers.unsubscribe import address_hash
from app.main import app
from app.storage import suppressed
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
