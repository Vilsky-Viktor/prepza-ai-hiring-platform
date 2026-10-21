import pytest
from fastapi import HTTPException
from prepza_common.superadmin import is_superadmin, superadmin_user
from prepza_common.user import User


def user(email="Ann@Example.com", verified=True, provider="google.com"):
    return User(uid="ann", email=email, email_verified=verified, sign_in_provider=provider)


@pytest.fixture(autouse=True)
def admins(monkeypatch):
    monkeypatch.setenv("SUPERADMIN_EMAILS", " ann@example.com, bob@example.com ")


def test_a_listed_verified_email_is_a_superadmin_whatever_its_case():
    assert is_superadmin(user())


def test_an_unverified_or_unlisted_account_is_not():
    assert not is_superadmin(user(verified=False))
    assert not is_superadmin(user("eve@example.com"))


@pytest.mark.parametrize("provider", ["github.com", "password", "custom", None])
def test_a_listed_address_signed_in_other_than_with_google_is_not(provider):
    assert not is_superadmin(user(provider=provider))

    with pytest.raises(HTTPException) as refused:
        superadmin_user(user(provider=provider))

    assert refused.value.status_code == 404


def test_no_admins_when_the_setting_is_empty(monkeypatch):
    monkeypatch.setenv("SUPERADMIN_EMAILS", "")

    assert not is_superadmin(user(""))


def test_admin_routes_are_not_found_for_others_and_the_try_is_logged(caplog):
    with pytest.raises(HTTPException) as refused:
        superadmin_user(user("eve@example.com"))

    assert refused.value.status_code == 404
    [record] = caplog.records
    assert (record.levelname, record.getMessage()) == (
        "WARNING",
        "Admin zone refused to account ann",
    )
    assert superadmin_user(user()).uid == "ann"
