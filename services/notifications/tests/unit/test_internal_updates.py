import uuid
from datetime import UTC, datetime

from prepza_common.auth.service_auth import issue_token
from prepza_common.config.constants import UPDATES_CALLER

from app.models.notifications import Notification
from app.storage import updates

SECRET = "test-secret-that-is-at-least-32-bytes"
COMPANY = uuid.uuid4()
SINCE = "2026-10-17T09:00:00+00:00"
UNTIL = "2026-10-18T09:00:00+00:00"


def headers(caller: str) -> dict:
    return {"Authorization": f"Bearer {issue_token(caller, 'notifications', SECRET)}"}


def body(company_ids=None, since=SINCE) -> dict:
    ids = [COMPANY] if company_ids is None else company_ids

    return {"company_ids": [str(id) for id in ids], "since": since, "until": UNTIL}


def test_the_assistant_reads_its_companies_updates_with_each_ones_company(client, monkeypatch):
    asked = []
    row = Notification(
        id=uuid.uuid4(),
        recipient="company",
        recipient_id=str(COMPANY),
        kind="candidate_finished",
        link=f"/companies/{COMPANY}",
        data={"title": "Backend"},
        created_at=datetime(2026, 10, 18, 8, tzinfo=UTC),
    )

    async def of_companies(company_ids, since, until):
        asked.append((company_ids, since.isoformat(), until.isoformat()))

        return [row]

    monkeypatch.setattr(updates, "of_companies", of_companies)

    response = client.post("/internal/updates", json=body(), headers=headers(UPDATES_CALLER))

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": str(row.id),
                "kind": "candidate_finished",
                "link": f"/companies/{COMPANY}",
                "data": {"title": "Backend"},
                "created_at": "2026-10-18T08:00:00Z",
                "company_id": str(COMPANY),
            }
        ]
    }
    assert asked == [([str(COMPANY)], SINCE, UNTIL)]


def test_no_companies_give_no_updates_without_reading(client, monkeypatch):
    async def of_companies(company_ids, since, until):
        raise AssertionError("read")

    monkeypatch.setattr(updates, "of_companies", of_companies)

    response = client.post("/internal/updates", json=body([]), headers=headers(UPDATES_CALLER))

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_another_service_is_not_allowed(client):
    response = client.post("/internal/updates", json=body(), headers=headers("library"))

    assert response.status_code == 403
    assert response.json()["detail"] == "Not allowed"


def test_a_call_without_a_token_is_refused(client):
    response = client.post("/internal/updates", json=body())

    assert response.status_code == 401


def test_a_time_without_a_time_zone_is_refused(client):
    response = client.post(
        "/internal/updates", json=body(since="2026-10-17T09:00:00"), headers=headers(UPDATES_CALLER)
    )

    assert response.status_code == 422
