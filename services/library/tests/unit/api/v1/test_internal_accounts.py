"""Accounts' `user.deleted` deletes, and accounts' export call reads, a user's data in library:
their votes and reports on questions; the export only with library's own key, the email in the
body."""

import pytest
from event_pushes import push
from testee_common.http.http import bearer

from library.api.v1 import internal_accounts
from library.handlers import user_deleted
from tests.unit.api.v1.test_internal import token

BODY = {"email": "ann@example.com"}


@pytest.fixture
def stored(monkeypatch):
    done = []

    async def delete_data(user_id):
        done.append(user_id)

    async def export_data(user_id):
        return {"question_votes": [{"question": "Why?", "vote": 1}], "question_reports": []}

    monkeypatch.setattr(user_deleted, "delete_data", delete_data)
    monkeypatch.setattr(internal_accounts, "export_data", export_data)

    return done


def test_a_deleted_account_takes_the_users_votes_and_reports(client, stored):
    gone = push("user.deleted", {"user_id": "ann", **BODY})
    response = client.post("/internal/events", json=gone)

    assert (response.status_code, stored) == (204, ["ann"])


def test_an_export_gives_the_users_votes_and_reports(client, stored):
    response = client.post("/internal/users/ann/export", json=BODY, headers=bearer(token()))

    assert response.json() == {
        "question_votes": [{"question": "Why?", "vote": 1}],
        "question_reports": [],
    }
