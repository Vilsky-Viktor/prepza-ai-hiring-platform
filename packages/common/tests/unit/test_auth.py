from unittest import mock

import pytest
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from firebase_admin import auth as firebase_auth
from prepza_common.auth import current_user, optional_user, verify
from prepza_common.constants import SIGN_IN_UNAVAILABLE

CLAIMS = {"uid": "ann", "email": "ann@example.com", "email_verified": True, "name": "Ann"}


def test_a_valid_token_gives_its_user():
    with mock.patch.object(firebase_auth, "verify_id_token", return_value=CLAIMS):
        user = verify("token")

    assert (user.uid, user.email, user.email_verified, user.name) == (
        "ann",
        "ann@example.com",
        True,
        "Ann",
    )


@pytest.mark.parametrize(
    "error", [ValueError("malformed"), firebase_auth.InvalidIdTokenError("bad", cause=None)]
)
def test_an_invalid_token_gives_no_user(error):
    with mock.patch.object(firebase_auth, "verify_id_token", side_effect=error):
        assert verify("token") is None


def test_unreachable_certificates_are_a_503_not_a_bad_token():
    error = firebase_auth.CertificateFetchError("down", cause=None)

    with (
        mock.patch.object(firebase_auth, "verify_id_token", side_effect=error),
        pytest.raises(HTTPException) as raised,
    ):
        verify("token")

    assert raised.value.status_code == 503
    assert raised.value.detail == SIGN_IN_UNAVAILABLE


def request(method: str) -> Request:
    return Request({"type": "http", "method": method, "headers": []})


CREDENTIALS = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")


def test_a_signed_in_request_names_the_user_to_sentry_by_id_only():
    with (
        mock.patch.object(firebase_auth, "verify_id_token", return_value=CLAIMS),
        mock.patch("sentry_sdk.set_user") as set_user,
    ):
        current_user(request("GET"), CREDENTIALS)

    set_user.assert_called_once_with({"id": "ann"})


@pytest.mark.parametrize(
    ("method", "checked"),
    [("GET", False), ("HEAD", False), ("POST", True), ("PUT", True), ("DELETE", True)],
)
def test_only_a_change_asks_firebase_whether_the_sign_in_was_revoked(method, checked):
    with mock.patch.object(firebase_auth, "verify_id_token", return_value=CLAIMS) as verified:
        current_user(request(method), CREDENTIALS)
        optional_user(request(method), CREDENTIALS)

    assert [call.kwargs["check_revoked"] for call in verified.call_args_list] == [checked] * 2


@pytest.mark.parametrize(
    "error",
    [
        firebase_auth.RevokedIdTokenError("revoked"),
        firebase_auth.UserNotFoundError("deleted"),
        firebase_auth.UserDisabledError("disabled"),
    ],
)
def test_a_deleted_or_revoked_account_cant_change_anything(error):
    with (
        mock.patch.object(firebase_auth, "verify_id_token", side_effect=error),
        pytest.raises(HTTPException) as raised,
    ):
        current_user(request("POST"), CREDENTIALS)

    assert raised.value.status_code == 401


def test_firebase_unreachable_while_checking_revocation_is_a_503():
    error = firebase_auth.UnexpectedResponseError("down", cause=None, http_response=None)

    with (
        mock.patch.object(firebase_auth, "verify_id_token", side_effect=error),
        pytest.raises(HTTPException) as raised,
    ):
        current_user(request("POST"), CREDENTIALS)

    assert raised.value.status_code == 503
    assert raised.value.detail == SIGN_IN_UNAVAILABLE
