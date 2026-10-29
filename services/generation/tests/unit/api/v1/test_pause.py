import uuid

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User
from prepza_common.config.constants import PAUSED
from prepza_common.http.http import bearer

from generation.core.security import service_token
from generation.main import app


@pytest.fixture(autouse=True)
def paused(monkeypatch):
    """The switch on, and Ann, a superadmin, signed in."""

    async def on(redis):
        return True

    monkeypatch.setattr("prepza_common.limits.pause.is_paused", on)
    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")
    app.dependency_overrides[current_user] = lambda: User(
        uid="ann",
        email="ann@example.com",
        email_verified=True,
        sign_in_provider="google.com",
    )
    yield
    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "path, body",
    [
        ("/superadmin/templates", {"text": "Senior accountant"}),
        (f"/superadmin/generations/{uuid.uuid4()}/review", {"selected": [0]}),
        (f"/superadmin/generations/{uuid.uuid4()}/retry", None),
        (f"/superadmin/templates/{uuid.uuid4()}/questions/{uuid.uuid4()}/regenerate", None),
    ],
)
def test_paused_new_templates_and_regenerations_are_refused(client, queued, path, body):
    refused = client.post(path, json=body)

    assert refused.status_code == 503
    assert refused.json()["detail"] == PAUSED
    assert queued == []


def test_paused_the_verifier_takes_no_new_question(client, queued):
    refused = client.post(
        f"/internal/questions/{uuid.uuid4()}/verify",
        json={"flag": "wrong_key", "now": True},
        headers=bearer(service_token("generation")),
    )

    assert refused.status_code == 503
    assert queued == []


@pytest.mark.parametrize(
    "kind, source",
    [
        ("campaigns", {"subject": "New", "text": "One.", "button": None, "missing": ["de"]}),
        ("news", {"title": "New", "text": "One.", "missing": ["de"]}),
    ],
)
def test_paused_a_campaign_or_news_post_is_not_queued_for_translation(
    client, batch_store, kind, source
):
    """Notifications saves a campaign again later, and site's daily run sends a post again."""
    refused = client.post(
        f"/internal/{kind}/{uuid.uuid4()}/translate",
        json=source,
        headers=bearer(service_token("generation")),
    )

    assert refused.status_code == 503
    assert batch_store.rows == {}
