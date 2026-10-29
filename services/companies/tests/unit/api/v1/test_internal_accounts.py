from prepza_common.auth.service_auth import issue_token
from prepza_common.http.http import bearer

from companies.repositories import accounts, companies
from companies.services import accounts as account_service

URL = "/internal/users/ann/companies"
HEADERS = {
    "Authorization": "Bearer "
    + issue_token("accounts", "companies", "test-secret-that-is-at-least-32-bytes")
}
BODY = {"email": "ann@example.com"}


def test_notifications_gets_every_company_of_a_user(client, monkeypatch):
    asked = []

    async def fake_ids(session, user_id):
        asked.append(user_id)

        return ["acme", "globex"]

    monkeypatch.setattr(companies, "ids_for_user", fake_ids)
    token = issue_token("notifications", "companies", "test-secret-that-is-at-least-32-bytes")

    response = client.get(URL, headers=bearer(token))

    assert response.status_code == 200
    assert response.json() == {"company_ids": ["acme", "globex"]}
    assert asked == ["ann"]


def test_deleting_and_exporting_an_account_read_the_email_from_the_body(client, monkeypatch):
    asked = []

    async def delete_user(user_id, email):
        asked.append(("delete", user_id, email))

    async def export(session, user_id, email):
        asked.append(("export", user_id, email))

        return {"company_memberships": []}

    monkeypatch.setattr(account_service, "delete_user", delete_user)
    monkeypatch.setattr(accounts, "export", export)

    deleted = client.request("DELETE", "/internal/users/ann", json=BODY, headers=HEADERS)
    exported = client.post("/internal/users/ann/export", json=BODY, headers=HEADERS)

    assert deleted.status_code == 204
    assert exported.json() == {"company_memberships": []}
    assert asked == [
        ("delete", "ann", "ann@example.com"),
        ("export", "ann", "ann@example.com"),
    ]
