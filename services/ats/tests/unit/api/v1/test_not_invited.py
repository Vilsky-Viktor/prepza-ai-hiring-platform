import asyncio
import uuid
from datetime import UTC, datetime

from testee_common.auth.service_auth import issue_token
from testee_common.config.constants import MAX_UPDATES
from testee_common.http.http import bearer

from ats.constants.ats import AtsProvider, CandidateStatus, FailReason
from ats.integrations import companies
from ats.models.ats import AtsCandidate, AtsConnection
from ats.repositories import not_invited
from ats.services.not_invited import not_invited_between

SECRET = "test-secret-that-is-at-least-32-bytes"
SINCE = datetime(2026, 10, 1, tzinfo=UTC)
UNTIL = datetime(2026, 10, 18, tzinfo=UTC)
COMPANY = uuid.uuid4()
KNOWN = uuid.uuid4()
UNKNOWN = uuid.uuid4()


def candidate(interview_id, email, name, at, reason) -> AtsCandidate:
    return AtsCandidate(
        interview_id=interview_id,
        email=email,
        name=name,
        status=CandidateStatus.FAILED,
        reason=reason,
        failed_at=at,
    )


def connection(provider) -> AtsConnection:
    return AtsConnection(id=uuid.uuid4(), company_id=COMPANY, provider=provider)


def fake(monkeypatch):
    """Two candidates not invited: one for an interview companies knows, one it doesn't."""
    asked = {}
    newer = datetime(2026, 10, 17, tzinfo=UTC)
    older = datetime(2026, 10, 2, tzinfo=UTC)
    rows = [
        (
            candidate(KNOWN, "ann@example.com", "Ann Lee", newer, FailReason.LIMIT),
            connection(AtsProvider.BREEZY),
        ),
        (
            candidate(UNKNOWN, "bob@example.com", None, older, FailReason.CREDITS),
            connection(AtsProvider.WORKABLE),
        ),
    ]

    async def between(session, company_ids, since, until, limit):
        asked["between"] = (company_ids, since, until, limit)

        return rows

    async def count_between(session, company_ids, since, until):
        return 7

    async def interviews(ids):
        asked["interviews"] = ids

        return {KNOWN: {"id": str(KNOWN), "title": "Accountant"}}

    monkeypatch.setattr(not_invited, "between", between)
    monkeypatch.setattr(not_invited, "count_between", count_between)
    monkeypatch.setattr(companies, "interviews", interviews)

    return asked


def test_each_candidate_not_invited_comes_with_its_interview_ats_link_and_reason(monkeypatch):
    asked = fake(monkeypatch)
    found = asyncio.run(not_invited_between([COMPANY], SINCE, UNTIL))

    assert asked == {
        "between": ([COMPANY], SINCE, UNTIL, MAX_UPDATES),
        "interviews": {KNOWN, UNKNOWN},
    }
    assert found.total == 7
    assert [item.model_dump() for item in found.items] == [
        {
            "at": datetime(2026, 10, 17, tzinfo=UTC),
            "company_id": COMPANY,
            "interview_id": KNOWN,
            "title": "Accountant",
            "ats": "Breezy HR",
            "email": "ann@example.com",
            "candidate_name": "Ann Lee",
            "reason": FailReason.LIMIT,
            "link": f"/companies/{COMPANY}/integrations/breezy",
        },
        {
            "at": datetime(2026, 10, 2, tzinfo=UTC),
            "company_id": COMPANY,
            "interview_id": UNKNOWN,
            # Companies doesn't know the interview (deleted meanwhile): no title.
            "title": None,
            "ats": "Workable",
            "email": "bob@example.com",
            "candidate_name": None,
            "reason": FailReason.CREDITS,
            "link": f"/companies/{COMPANY}/integrations/workable",
        },
    ]


def post(client, caller=None):
    body = {"company_ids": [str(COMPANY)], "since": SINCE.isoformat(), "until": UNTIL.isoformat()}
    headers = bearer(issue_token(caller, "ats", SECRET)) if caller else {}

    return client.post("/internal/candidates/not-invited", json=body, headers=headers)


def test_the_assistant_gets_the_candidates_not_invited(client, monkeypatch):
    fake(monkeypatch)
    response = post(client, "assistant")

    assert response.status_code == 200
    assert [(item["email"], item["title"], item["ats"]) for item in response.json()["items"]] == [
        ("ann@example.com", "Accountant", "Breezy HR"),
        ("bob@example.com", None, "Workable"),
    ]
    # How many in all, not only those listed.
    assert response.json()["total"] == 7


def test_another_service_is_refused_and_a_call_without_a_token_is_unauthorized(client, monkeypatch):
    fake(monkeypatch)
    refused = post(client, "library")

    assert refused.status_code == 403
    assert refused.json()["detail"] == "Not allowed"
    assert post(client).status_code == 401
