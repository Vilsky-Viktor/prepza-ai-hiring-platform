"""Accounts deleting or exporting a user's data in library: their votes and reports on
questions, only with library's own key, the email in the body."""

import pytest
from prepza_common.http.http import bearer

from library.api.v1 import internal_accounts
from tests.unit.api.v1.test_internal import token

BODY = {"email": "ann@example.com"}


@pytest.fixture
def stored(monkeypatch):
    done = []

    async def delete_data(user_id):
        done.append(user_id)

    async def export_data(user_id):
        return {"question_votes": [{"question": "Why?", "vote": 1}], "question_reports": []}

    monkeypatch.setattr(internal_accounts, "delete_data", delete_data)
    monkeypatch.setattr(internal_accounts, "export_data", export_data)

    return done


def test_a_deletion_removes_the_users_votes_and_reports(client, stored):
    response = client.request("DELETE", "/internal/users/ann", json=BODY, headers=bearer(token()))

    assert (response.status_code, stored) == (204, ["ann"])


def test_an_export_gives_the_users_votes_and_reports(client, stored):
    response = client.post("/internal/users/ann/export", json=BODY, headers=bearer(token()))

    assert response.json() == {
        "question_votes": [{"question": "Why?", "vote": 1}],
        "question_reports": [],
    }


def test_a_call_without_librarys_key_is_refused(client, stored):
    response = client.request("DELETE", "/internal/users/ann", json=BODY)

    assert (response.status_code, stored) == (401, [])
