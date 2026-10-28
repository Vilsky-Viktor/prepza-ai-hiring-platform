import uuid
from types import SimpleNamespace

from prepza_common.auth.service_auth import issue_token
from prepza_common.events.notifications import notification
from prepza_common.http.http import bearer

from companies.repositories import interviews, invite_progress, invites
from companies.services import outbox as outbox_service

INVITE_ID = uuid.uuid4()
URL = f"/internal/invites/{INVITE_ID}/undelivered"
INTERVIEW = SimpleNamespace(id=uuid.uuid4(), company_id=uuid.uuid4(), title="Backend")


def test_notifications_marks_an_invite_undelivered_and_the_company_is_told(client, monkeypatch):
    marked = []

    async def fake_get(session, invite_id):
        return SimpleNamespace(
            id=invite_id, interview_id=INTERVIEW.id, email="erin@example.com", name=None
        )

    async def fake_interview(session, interview_id):
        return INTERVIEW

    async def fake_mark(session, invite_id, notice):
        marked.append((invite_id, notice))

    async def no_flush():
        pass

    monkeypatch.setattr(invites, "get", fake_get)
    monkeypatch.setattr(interviews, "get", fake_interview)
    monkeypatch.setattr(invite_progress, "mark_undelivered", fake_mark)
    monkeypatch.setattr(outbox_service, "flush_quietly", no_flush)
    token = issue_token("notifications", "companies", "test-secret-that-is-at-least-32-bytes")

    company = INTERVIEW.company_id
    undelivered = notification(
        "company",
        company,
        "invite_undelivered",
        f"/companies/{company}/interviews/{INTERVIEW.id}",
        email="erin@example.com",
        title="Backend",
        # Slack opens the candidate, where the invite is resent.
        candidate_link=f"/companies/{company}/interviews/{INTERVIEW.id}/candidates/{INVITE_ID}",
    )
    assert client.post(URL, headers=bearer(token)).status_code == 204
    assert marked == [(INVITE_ID, undelivered)]


def test_marking_needs_a_service_token(client):
    assert client.post(URL).status_code in (401, 403)


def test_notifications_asks_which_companies_invited_an_address(client, monkeypatch):
    asked = []

    async def fake_company_ids(session, email):
        asked.append(email)

        return ["c-1"]

    monkeypatch.setattr(invites, "company_ids_for", fake_company_ids)
    token = issue_token("notifications", "companies", "test-secret-that-is-at-least-32-bytes")

    response = client.post(
        "/internal/invites/companies",
        json={"email": "ann@example.com"},
        headers=bearer(token),
    )

    assert response.json() == {"company_ids": ["c-1"]}
    assert asked == ["ann@example.com"]


def test_asking_which_companies_invited_an_address_needs_a_service_token(client):
    response = client.post("/internal/invites/companies", json={"email": "ann@example.com"})

    assert response.status_code in (401, 403)
