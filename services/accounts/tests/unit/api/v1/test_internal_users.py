"""Another service deleting or exporting an account's data here: only with accounts' own key,
the email in the body."""

import pytest
from prepza_common.http.http import bearer

from accounts.api.v1 import internal_users
from tests.unit.tokens import token

AUTH = bearer(token())
BODY = {"email": "ann@example.com"}


@pytest.fixture
def stored(monkeypatch):
    done = []

    async def delete_data(user_id):
        done.append(("deleted", user_id))

    async def export_data(user_id):
        return {"terms_accepted": [{"version": "2026-10-10", "at": "2026-10-11T00:00:00Z"}]}

    monkeypatch.setattr(internal_users, "delete_data", delete_data)
    monkeypatch.setattr(internal_users, "export_data", export_data)

    return done


def test_a_deletion_removes_the_accounts_data(client, stored):
    response = client.request("DELETE", "/internal/users/ann", json=BODY, headers=AUTH)

    assert response.status_code == 204
    assert stored == [("deleted", "ann")]


def test_an_export_gives_the_accounts_data(client, stored):
    response = client.post("/internal/users/ann/export", json=BODY, headers=AUTH)

    assert response.json() == {
        "terms_accepted": [{"version": "2026-10-10", "at": "2026-10-11T00:00:00Z"}]
    }


@pytest.mark.parametrize("headers", [{}, bearer(token("another-secret-at-least-32-bytes-long"))])
def test_a_call_without_accounts_key_is_refused(client, stored, headers):
    response = client.request("DELETE", "/internal/users/ann", json=BODY, headers=headers)

    assert response.status_code == 401
    assert stored == []
