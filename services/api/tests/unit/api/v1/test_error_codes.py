"""Every refusal of the public API carries a stable `code` beside its translated `detail`."""

from datetime import UTC, datetime, timedelta

# The key fixture is imported from test_public_routes and named in the tests.
# ruff: noqa: F811
import pytest
from prepza_common.i18n.i18n import CodedError

from api.integrations import companies
from tests.unit.api.v1.test_api_changes import changes, post  # noqa: F401 (fixture)
from tests.unit.api.v1.test_public_routes import call, key  # noqa: F401 (fixture)
from tests.unit.conftest import INTERVIEW


def test_a_missing_or_expired_key_or_a_creator_without_access_says_which(
    client, companies_api, key
):
    missing = call(client, "GET", "/interviews", key="pz_unknown")
    key.expires_at = datetime.now(UTC) - timedelta(days=1)
    expired = call(client, "GET", "/interviews")
    key.expires_at = None
    companies_api["roles"]["u1"] = "viewer"
    lost = call(client, "GET", "/interviews")

    assert [(item.status_code, item.json()) for item in (missing, expired, lost)] == [
        (401, {"detail": "Invalid API key", "code": "invalid_api_key"}),
        (401, {"detail": "This API key has expired", "code": "api_key_expired"}),
        (
            401,
            {
                "detail": "This key's creator is no longer an owner or admin of the company",
                "code": "key_creator_lost_access",
            },
        ),
    ]


def test_a_refusal_without_its_own_code_carries_its_statuss(client, companies_api, key):
    companies_api["missing"] = True
    response = call(client, "GET", f"/interviews/{INTERVIEW}")

    assert (response.status_code, response.json()["code"]) == (404, "not_found")


def test_a_validation_error_has_a_code_and_still_names_each_field(client, companies_api, key):
    response = call(client, "POST", f"/interviews/{INTERVIEW}/candidates", json={"email": "x"})

    assert (response.status_code, response.json()["code"]) == (422, "validation_failed")
    assert [item["loc"] for item in response.json()["detail"]] == [["body", "email"]]


@pytest.mark.parametrize(
    ("status", "detail", "code"),
    [
        (409, "The interview isn't ready yet", "interview_not_ready"),
        (402, "Not enough credits.", "insufficient_credits"),
        (503, "Paused.", "paused"),
    ],
)
def test_companies_refusals_reach_the_client_with_their_code(
    client, companies_api, key, monkeypatch, status, detail, code
):
    async def refuse(*args, **kwargs):
        raise CodedError(status, detail, code)

    monkeypatch.setattr(companies, "invite", refuse)
    response = call(
        client, "POST", f"/interviews/{INTERVIEW}/candidates", json={"email": "a@example.com"}
    )

    assert (response.status_code, response.json()) == (status, {"detail": detail, "code": code})


def test_a_reused_or_running_idempotency_key_says_so(client, companies_api, key, changes):
    path = f"/interviews/{INTERVIEW}/candidates"
    post(client, path, {"email": "bob@example.com"}, "k-1")
    reused = post(client, path, {"email": "eve@example.com"}, "k-1")

    assert (reused.status_code, reused.json()["code"]) == (422, "idempotency_key_reused")
