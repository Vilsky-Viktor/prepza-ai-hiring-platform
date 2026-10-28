"""Deleting a sign-in (services/accounts.py): revoked first, and safe when it's gone already."""

from accounts.services import accounts as account_service


def test_deleting_the_sign_in_revokes_it_first(monkeypatch):
    done = []
    monkeypatch.setattr(
        account_service.firebase_auth,
        "revoke_refresh_tokens",
        lambda uid: done.append(("revoked", uid)),
    )
    monkeypatch.setattr(
        account_service.firebase_auth, "delete_user", lambda uid: done.append(("deleted", uid))
    )

    account_service.delete_sign_in("ann")

    assert done == [("revoked", "ann"), ("deleted", "ann")]


def test_a_sign_in_already_gone_is_deleted(monkeypatch):
    def gone(uid):
        raise account_service.firebase_auth.UserNotFoundError("gone")

    monkeypatch.setattr(account_service.firebase_auth, "revoke_refresh_tokens", gone)

    account_service.delete_sign_in("ann")
