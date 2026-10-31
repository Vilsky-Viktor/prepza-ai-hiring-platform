import base64
import uuid
from datetime import UTC, datetime

import pytest
from fake_redis import FakeRedis
from testee_common.auth.auth import current_user
from testee_common.auth.user import User

from companies.constants.reports import (
    NO_FINISHED_CANDIDATES,
    OUTSIDE_COMPANY,
    TOO_MANY_REPORT_EMAILS,
)
from companies.integrations import rounds
from companies.main import app
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import audit, companies, interviews, reports
from companies.services import outbox as outbox_service
from companies.services import report_emails
from tests.unit import fake_candidates

COMPANY_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()
INVITE_ID = uuid.uuid4()
URL = f"/interviews/{INTERVIEW_ID}/candidates/{INVITE_ID}/report/email"
PDF = base64.b64encode(b"%PDF-1.3 a report").decode()


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def queued(monkeypatch):
    """A member's candidate; returns the events queued for notifications."""
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True, name="Bob"
    )
    invite = CandidateInvite(
        id=INVITE_ID,
        interview_id=INTERVIEW_ID,
        email="ann@example.com",
        name="Ann Lee",
        token="token-ann",
        status="finished",
        created_at=datetime.now(UTC),
    )
    interview = Interview(
        pass_mark=70,
        id=INTERVIEW_ID,
        company_id=COMPANY_ID,
        generation_id=uuid.uuid4(),
        set_id=uuid.uuid4(),
        title="Backend",
        language="en",
    )
    fake_candidates.add(invite)
    company = Company(id=COMPANY_ID, name="Arcolabs", created_at=datetime.now(UTC))
    company.members = [
        Member(company_id=COMPANY_ID, user_id="bob", invited_email="bob@example.com", role="admin"),
        Member(company_id=COMPANY_ID, user_id="cy", invited_email="Cy@Example.com", role="viewer"),
        # Invited, not joined yet.
        Member(company_id=COMPANY_ID, user_id=None, invited_email="dan@example.com", role="admin"),
    ]
    events = []

    async def fake_interview(session, _interview_id):
        return interview

    async def fake_company(session, _company_id):
        return company

    async def fake_queue(session, data):
        events.append(data)

    async def no_flush():
        return None

    monkeypatch.setattr(interviews, "get", fake_interview)
    monkeypatch.setattr(companies, "get", fake_company)
    monkeypatch.setattr(reports, "queue_email", fake_queue)
    redis = FakeRedis()
    monkeypatch.setattr(report_emails, "get_redis", lambda: redis)
    monkeypatch.setattr(outbox_service, "flush_quietly", no_flush)

    return events


def test_a_member_emails_the_pdf_report_and_replies_go_to_them(client, queued):
    response = client.post(URL, json={"email": "Boss@Example.com", "pdf": PDF})

    assert response.status_code == 202
    [event] = queued
    assert (event["email"], event["sender"], event["reply_to"]) == (
        "boss@example.com",
        "Bob",
        "bob@example.com",
    )
    # The candidate as the email names them: their name, with the email.
    assert (event["candidate"], event["company"], event["title"]) == (
        "Ann Lee (ann@example.com)",
        "Arcolabs",
        "Backend",
    )
    assert event["pdf"] == PDF


def test_replies_go_to_testees_inbox_while_the_senders_email_isnt_verified(client, queued):
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=False, name="Bob"
    )

    assert client.post(URL, json={"email": "boss@example.com", "pdf": PDF}).status_code == 202
    assert queued[0]["reply_to"] is None


def test_a_report_email_is_in_the_senders_language_not_the_tests(client, queued):
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True, name="Bob", language="de"
    )

    client.post(URL, json={"email": "boss@example.com", "pdf": PDF})

    [event] = queued
    assert event["language"] == "de"


def test_only_a_pdf_is_emailed(client, queued):
    not_pdf = base64.b64encode(b"<html>hello</html>").decode()

    assert client.post(URL, json={"email": "boss@example.com", "pdf": not_pdf}).status_code == 422
    assert client.post(URL, json={"email": "boss@example.com", "pdf": "%%%"}).status_code == 422
    assert queued == []


def test_the_tests_report_lists_candidates_as_storage_orders_them(client, queued, monkeypatch):
    def invite(email, status):
        return CandidateInvite(
            id=uuid.uuid4(),
            interview_id=INTERVIEW_ID,
            email=email,
            token=f"t-{email}",
            status=status,
            created_at=datetime.now(UTC),
        )

    # Best grade first, deleted ones left out: storage's order (see the integration tests).
    everyone = [invite("top@example.com", "finished"), invite("low@example.com", "finished")]
    fake_candidates.ROWS[:] = everyone
    grades = {"low@example.com": 40, "top@example.com": 90}

    async def fake_scores(invite_ids):
        return {
            str(row.id): {"progress": 100, "grade": grades[row.email], "finished": True}
            for row in everyone
            if row.id in invite_ids
        }

    monkeypatch.setattr(rounds, "invite_scores", fake_scores)

    report = client.get(f"/interviews/{INTERVIEW_ID}/report").json()

    assert (report["company"], report["pass_mark"]) == ("Arcolabs", 70)
    assert [(row["email"], row["passed"]) for row in report["candidates"]] == [
        ("top@example.com", True),
        ("low@example.com", False),
    ]


def test_the_tests_report_is_emailed_as_a_candidates_report(client, queued):
    response = client.post(
        f"/interviews/{INTERVIEW_ID}/report/email", json={"email": "boss@example.com", "pdf": PDF}
    )

    assert response.status_code == 202
    [event] = queued
    # Notifications names the attachment, in the email's language.
    assert (event["kind"], event["title"]) == ("candidates", "Backend")
    assert "filename" not in event
    assert "candidate" not in event


def test_no_report_is_emailed_before_a_candidate_finishes(client, queued, monkeypatch):
    unfinished = CandidateInvite(
        id=INVITE_ID,
        interview_id=INTERVIEW_ID,
        email="ann@example.com",
        token="token-ann",
        status="in_process",
        created_at=datetime.now(UTC),
    )
    interview = Interview(id=INTERVIEW_ID, company_id=COMPANY_ID, title="Backend", language="en")
    fake_candidates.ROWS[:] = [unfinished]

    async def fake_interview(session, _interview_id):
        return interview

    monkeypatch.setattr(interviews, "get", fake_interview)
    body = {"email": "boss@example.com", "pdf": PDF}

    refused = client.post(URL, json=body)
    refused_all = client.post(f"/interviews/{INTERVIEW_ID}/report/email", json=body)

    assert (refused.status_code, refused_all.status_code) == (409, 409)
    assert refused.json()["detail"] == NO_FINISHED_CANDIDATES
    assert queued == []


@pytest.mark.parametrize(("edited", "most"), [(None, 20), (2, 2)])
def test_a_company_emails_a_limited_number_of_reports_a_day(
    client, queued, monkeypatch, limit_hits, edited, most
):
    redis = FakeRedis({"REPORT_EMAILS_PER_COMPANY_DAY": edited} if edited else None)

    async def nothing(session, *args, **kwargs):
        return None

    monkeypatch.setattr(report_emails, "get_redis", lambda: redis)
    # The action log isn't what this test checks.
    monkeypatch.setattr(audit, "record", nothing)

    def send(number):
        return client.post(URL, json={"email": f"boss{number}@example.com", "pdf": PDF})

    assert [send(number).status_code for number in range(most)] == [202] * most

    refused = send(most)

    assert refused.status_code == 429
    assert refused.json()["detail"] == TOO_MANY_REPORT_EMAILS
    assert len(queued) == most
    assert [(hit["limit"], hit["company_id"], hit["user_id"]) for hit in limit_hits] == [
        ("REPORT_EMAILS_PER_COMPANY_DAY", str(COMPANY_ID), "bob")
    ]


@pytest.mark.parametrize("url", [URL, f"/interviews/{INTERVIEW_ID}/report/email"])
def test_a_viewer_emails_reports_only_to_the_companys_members(client, queued, url):
    app.dependency_overrides[current_user] = lambda: User(
        uid="cy", email="cy@example.com", email_verified=True, name="Cy"
    )

    def send(email):
        return client.post(url, json={"email": email, "pdf": PDF})

    outside = send("boss@example.com")
    invited_only = send("dan@example.com")
    member = send("Bob@Example.com")

    assert (outside.status_code, invited_only.status_code) == (403, 403)
    assert outside.json()["detail"] == OUTSIDE_COMPANY
    assert member.status_code == 202
    assert [event["email"] for event in queued] == ["bob@example.com"]
