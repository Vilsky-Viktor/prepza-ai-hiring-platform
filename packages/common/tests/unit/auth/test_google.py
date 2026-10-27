from unittest import mock

import pytest
from fastapi import HTTPException
from prepza_common.auth import google
from prepza_common.auth.google import verify_invoker

AUDIENCE = "https://companies.run.app"
INVOKER = "invoker@prepza.iam.gserviceaccount.com"


def request_with(token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    return mock.Mock(headers=headers)


@pytest.fixture
def production(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "prepza-prod")
    monkeypatch.setenv("INVOKER_AUDIENCE", AUDIENCE)
    monkeypatch.setenv("INVOKER_SERVICE_ACCOUNT", INVOKER)


def test_nothing_is_checked_locally(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "demo-prepza")

    verify_invoker(request_with())


def test_without_a_token_google_calls_are_refused(production):
    with pytest.raises(HTTPException) as refused:
        verify_invoker(request_with())

    assert refused.value.status_code == 401


@pytest.mark.parametrize(
    ("claims", "status"),
    [
        ({"email": INVOKER, "email_verified": True}, None),
        ({"email": "someone@example.com", "email_verified": True}, 403),
        ({"email": INVOKER, "email_verified": False}, 403),
    ],
    ids=["invoker", "another account", "unverified"],
)
def test_only_the_invoker_for_this_service_is_admitted(production, claims, status):
    with mock.patch.object(google.id_token, "verify_oauth2_token", return_value=claims) as check:
        if status is None:
            verify_invoker(request_with("signed"))
        else:
            with pytest.raises(HTTPException) as refused:
                verify_invoker(request_with("signed"))

            assert refused.value.status_code == status

    assert check.call_args.args[2] == AUDIENCE


def test_certificates_are_fetched_through_one_cached_transport(production):
    claims = {"email": INVOKER, "email_verified": True}

    with mock.patch.object(google.id_token, "verify_oauth2_token", return_value=claims) as check:
        verify_invoker(request_with("signed"))
        verify_invoker(request_with("signed"))

    first, second = (call.args[1] for call in check.call_args_list)
    assert first is second
