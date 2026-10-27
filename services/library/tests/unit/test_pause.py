import uuid

from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User

from app.integrations import generation
from app.main import app


def test_paused_a_superadmin_cant_send_a_question_to_the_verifier(client, monkeypatch):
    sent = []

    async def on(redis):
        return True

    async def verify_question(question_id, flag, now=False):
        sent.append(question_id)

    monkeypatch.setattr("prepza_common.limits.pause.is_paused", on)
    monkeypatch.setattr(generation, "verify_question", verify_question)
    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")
    app.dependency_overrides[current_user] = lambda: User(
        uid="ann",
        email="ann@example.com",
        email_verified=True,
        sign_in_provider="google.com",
    )

    response = client.post(f"/superadmin/quality/{uuid.uuid4()}/fix")
    app.dependency_overrides.clear()

    assert response.status_code == 503
    assert sent == []
