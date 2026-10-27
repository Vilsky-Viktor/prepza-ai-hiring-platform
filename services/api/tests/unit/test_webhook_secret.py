"""A web hook's secret is rolled without losing it: the old one signs too for a while."""

import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta

# The fixtures are imported and named in the tests.
# ruff: noqa: F811
import pytest
from prepza_common.auth.encryption import decrypt, encrypt

from app.constants.api import SECRET_OVERLAP
from app.storage import webhooks
from tests.unit.conftest import COMPANY, KEY, sign_in
from tests.unit.test_manage_routes import HOOKS, public  # noqa: F401 (fixture)
from tests.unit.test_webhook_delivery import finish
from tests.unit.webhook_fakes import endpoints  # noqa: F401 (fixture)


@pytest.fixture
def rolled(monkeypatch, stored):
    """The rolls written, as (web hook id, user id), the fake web hook changed as the database
    would."""
    done = []

    async def rotate(company_id, webhook_id, sealed, until, user_id):
        hook = next(
            (
                item
                for item in stored["webhooks"]
                if (item.company_id, item.id) == (company_id, webhook_id)
            ),
            None,
        )

        if hook is not None:
            hook.previous_secret, hook.previous_until, hook.secret = hook.secret, until, sealed
            done.append((hook.id, user_id))

        return hook

    monkeypatch.setattr(webhooks, "rotate", rotate)

    return done


def test_an_owner_rolls_a_secret_shown_once_and_the_old_one_overlaps(
    client, companies_api, stored, public, rolled
):
    sign_in()
    made = client.post(HOOKS, json={"url": "https://example.com/x"}).json()
    hook = stored["webhooks"][0]
    response = client.post(f"/manage/webhooks/{hook.id}/secret?company_id={COMPANY}")
    answer = response.json()
    until = datetime.fromisoformat(answer["previous_until"])

    assert response.status_code == 200
    assert answer["secret"].startswith("whsec_") and answer["secret"] != made["secret"]
    assert decrypt(KEY, hook.secret) == answer["secret"]
    assert decrypt(KEY, hook.previous_secret) == made["secret"]
    assert abs(until - (datetime.now(UTC) + SECRET_OVERLAP)) < timedelta(minutes=1)
    assert rolled == [(hook.id, "u1")]


def test_a_viewer_cant_roll_a_secret_and_another_companys_web_hook_isnt_found(
    client, companies_api, stored, public, rolled
):
    sign_in()
    client.post(HOOKS, json={"url": "https://example.com/x"})
    hook = stored["webhooks"][0]
    missing = client.post(
        f"/manage/webhooks/{hook.id}/secret?company_id={COMPANY}".replace(
            str(hook.id), str(COMPANY)
        )
    )
    companies_api["roles"]["u1"] = "viewer"
    viewer = client.post(f"/manage/webhooks/{hook.id}/secret?company_id={COMPANY}")

    assert (missing.status_code, viewer.status_code) == (404, 403)
    assert rolled == []


def signed_with(header: str, body: dict, secret: str) -> bool:
    parts = header.split(",")
    timestamp = parts[0].removeprefix("t=")
    raw = json.dumps(body, separators=(",", ":")).encode()
    digest = hmac.new(secret.encode(), f"{timestamp}.".encode() + raw, hashlib.sha256).hexdigest()

    return f"v1={digest}" in parts[1:]


@pytest.mark.parametrize(
    ("ends_in", "both"), [(timedelta(hours=1), True), (-timedelta(hours=1), False)]
)
def test_while_the_overlap_lasts_both_secrets_sign(endpoints, ends_in, both):
    hook = endpoints["hook"]("https://a.example/x", secret="whsec_new")
    hook.previous_secret = encrypt(KEY, "whsec_old")
    hook.previous_until = datetime.now(UTC) + ends_in
    finish()
    [(_, body, header)] = endpoints["posted"]

    assert signed_with(header, body, "whsec_new")
    assert signed_with(header, body, "whsec_old") is both
