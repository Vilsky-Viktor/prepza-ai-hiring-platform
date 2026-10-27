import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from prepza_common.auth.service_auth import issue_token
from prepza_common.http.http import bearer

from app.storage import email_reminders

TOKEN = issue_token("notifications", "companies", "test-secret-that-is-at-least-32-bytes")
HEADERS = bearer(TOKEN)
COMPANY_ID = uuid.uuid4()


def test_members_say_who_can_act_and_leave_out_pending_invites(client, monkeypatch):
    async def with_members(company_ids):
        return [
            SimpleNamespace(
                id=COMPANY_ID,
                name="Acme",
                members=[
                    SimpleNamespace(user_id="ann", role="owner"),
                    SimpleNamespace(user_id="vic", role="viewer"),
                    SimpleNamespace(user_id=None, role="admin"),
                ],
            )
        ]

    monkeypatch.setattr(email_reminders, "with_members", with_members)

    response = client.post(
        "/internal/companies/members", json={"company_ids": [str(COMPANY_ID)]}, headers=HEADERS
    )

    assert response.json() == {
        "companies": [
            {
                "id": str(COMPANY_ID),
                "name": "Acme",
                "members": [
                    {"user_id": "ann", "editor": True},
                    {"user_id": "vic", "editor": False},
                ],
            }
        ]
    }


WINDOWS = {
    "ready_after": "2026-09-28T08:00:00+00:00",
    "ready_before": "2026-10-05T08:00:00+00:00",
    "started_after": "2026-09-23T08:00:00+00:00",
    "started_before": "2026-10-07T08:00:00+00:00",
}


def test_the_companies_with_waiting_interviews_come_a_page_at_a_time(client, monkeypatch):
    asked = []

    async def waiting_company_ids(ready, started, after, limit):
        asked.append((ready, started, after, limit))

        return [COMPANY_ID]

    monkeypatch.setattr(email_reminders, "waiting_company_ids", waiting_company_ids)

    response = client.get(
        "/internal/interviews/waiting/companies",
        params={**WINDOWS, "after": str(COMPANY_ID), "limit": 5},
        headers=HEADERS,
    )

    assert response.json() == {"company_ids": [str(COMPANY_ID)]}
    [(ready, started, after, limit)] = asked
    assert ready[1] == datetime(2026, 10, 5, 8, tzinfo=UTC)
    assert started[0] == datetime(2026, 9, 23, 8, tzinfo=UTC)
    assert (after, limit) == (COMPANY_ID, 5)


def test_waiting_interviews_of_some_companies_pass_the_windows_through(client, monkeypatch):
    calls = []
    row = SimpleNamespace(
        id=uuid.uuid4(),
        company_id=COMPANY_ID,
        title="Backend",
        generation_id=None,
        created_at=datetime(2026, 10, 1, tzinfo=UTC),
    )

    async def waiting_of(ready, started, company_ids):
        calls.append((ready, started, company_ids))

        return [row], []

    monkeypatch.setattr(email_reminders, "waiting_of", waiting_of)

    response = client.post(
        "/internal/interviews/waiting",
        json={**WINDOWS, "company_ids": [str(COMPANY_ID)]},
        headers=HEADERS,
    )

    assert response.status_code == 200
    assert response.json()["without_candidates"][0]["title"] == "Backend"
    assert response.json()["being_generated"] == []
    [(ready, _, company_ids)] = calls
    assert ready[1] == datetime(2026, 10, 5, 8, tzinfo=UTC)
    assert company_ids == [COMPANY_ID]


def test_these_routes_need_a_service_token(client):
    assert client.post("/internal/companies/members", json={"company_ids": []}).status_code in (
        401,
        403,
    )
