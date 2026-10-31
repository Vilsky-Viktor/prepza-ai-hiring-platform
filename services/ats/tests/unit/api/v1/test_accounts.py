import uuid
from datetime import UTC, datetime

from event_pushes import push
from testee_common.auth.service_auth import issue_token
from testee_common.http.http import bearer

from ats.models.ats import AtsCandidate, AtsConnection
from ats.repositories import ats, ats_candidates

SECRET = "test-secret-that-is-at-least-32-bytes"


def headers(callee="ats"):
    return bearer(issue_token("accounts", callee, SECRET))


def test_deleting_an_account_deletes_its_candidates_and_forgets_its_connections(
    client, monkeypatch
):
    done = []

    async def delete_email(session, email):
        done.append(("candidates", email))

    async def forget_maker(session, user_id):
        done.append(("connections", user_id))

        return []

    monkeypatch.setattr(ats_candidates, "delete_email", delete_email)
    monkeypatch.setattr(ats, "forget_maker", forget_maker)
    gone = push("user.deleted", {"user_id": "u-1", "email": "ann@example.com"})
    response = client.post("/internal/events", json=gone)

    assert response.status_code == 204
    assert done == [("candidates", "ann@example.com"), ("connections", "u-1")]


def test_an_export_lists_what_atss_sent_about_them(client, monkeypatch):
    interview_id, company_id = uuid.uuid4(), uuid.uuid4()
    at = datetime(2026, 1, 2, tzinfo=UTC)
    row = AtsCandidate(
        email="ann@example.com",
        name="Ann Lee",
        interview_id=interview_id,
        status="invited",
        reported_at=None,
        created_at=at,
    )

    async def of_email(session, email):
        return [row] if email == "ann@example.com" else []

    async def made_by(session, user_id):
        return [
            AtsConnection(company_id=company_id, provider="workable", account="acme", created_at=at)
        ]

    monkeypatch.setattr(ats_candidates, "of_email", of_email)
    monkeypatch.setattr(ats, "made_by", made_by)
    body = {"email": "ann@example.com"}
    response = client.post("/internal/users/u-1/export", json=body, headers=headers())

    assert response.json() == {
        "ats_candidates": [
            {
                "email": "ann@example.com",
                "name": "Ann Lee",
                "interview_id": str(interview_id),
                "status": "invited",
                "results_sent_at": None,
                "at": "2026-01-02T00:00:00+00:00",
            }
        ],
        "ats_connections": [
            {
                "company_id": str(company_id),
                "provider": "workable",
                "account": "acme",
                "at": "2026-01-02T00:00:00+00:00",
            }
        ],
    }


def test_only_services_signed_for_ats_get_in(client):
    url = "/internal/users/u-1/export"
    body = {"email": "ann@example.com"}

    assert client.post(url, json=body).status_code in (401, 403)
    assert client.post(url, json=body, headers=headers("billing")).status_code == 401
