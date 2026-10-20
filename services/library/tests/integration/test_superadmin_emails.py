from types import SimpleNamespace

import httpx
from firebase_admin import auth as firebase_auth
from prepza_common.auth import current_user
from prepza_common.user import User
from sqlalchemy import select

from app.main import app
from app.models.emails import EmailConsent
from app.storage import emails
from app.storage.db import Session

ACCOUNT = SimpleNamespace(uid="asked-by-email", email="asked@example.com")


def test_a_superadmin_turns_settings_off_once_logged_as_admin_with_their_id(run, monkeypatch):
    """Firebase knows the account; the database is real."""
    monkeypatch.setenv("SUPERADMIN_EMAILS", "sam@prepza.dev")
    monkeypatch.setattr(firebase_auth, "get_user_by_email", lambda email: ACCOUNT)
    monkeypatch.setattr(firebase_auth, "get_user", lambda uid: ACCOUNT)
    app.dependency_overrides[current_user] = lambda: User(
        uid="sam",
        email="sam@prepza.dev",
        email_verified=True,
        sign_in_provider="google.com",
    )
    off = {"updates": False, "promotions": False, "reminders": False}

    async def scenario():
        await emails.change(ACCOUNT.uid, {"updates": True, "promotions": True}, "sign_in")
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(transport=transport, base_url="http://library") as client:
            found = await client.post(
                "/superadmin/emails/lookup", json={"email": "Asked@Example.com"}
            )
            # The same button pressed twice changes nothing the second time.
            for _ in range(2):
                await client.put(
                    f"/superadmin/emails/{ACCOUNT.uid}/preferences", json={"changes": off}
                )

            again = await client.post(
                "/superadmin/emails/lookup", json={"email": "asked@example.com"}
            )

        async with Session() as session:
            rows = (
                await session.scalars(
                    select(EmailConsent)
                    .where(EmailConsent.user_id == ACCOUNT.uid, EmailConsent.source == "admin")
                    .order_by(EmailConsent.setting)
                )
            ).all()

        return found.json(), again.json(), rows

    try:
        found, again, rows = run(scenario())
    finally:
        app.dependency_overrides.clear()

    assert found["account"]["preferences"]["promotions"] is True
    assert {setting: again["account"]["preferences"][setting] for setting in off} == off
    assert [(row.setting, row.granted, row.changed_by) for row in rows] == [
        ("promotions", False, "sam"),
        ("reminders", False, "sam"),
        ("updates", False, "sam"),
    ]
