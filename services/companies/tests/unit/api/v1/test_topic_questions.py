import uuid
from datetime import UTC, datetime

import httpx
from fake_redis import FakeRedis
from testee_common.auth.auth import current_user
from testee_common.auth.user import User
from testee_common.events.audit_actions import AuditAction, TargetKind

import companies.services.question_steps as question_routes
from companies.integrations import billing, generation, library
from companies.main import app
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.repositories import companies, interviews

COMPANY_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()
TOPIC_ID = uuid.uuid4()
QUESTION_ID = uuid.uuid4()


def sign_in():
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True, name="Bob"
    )


def interview_and_company(role):
    interview = Interview(
        id=INTERVIEW_ID,
        company_id=COMPANY_ID,
        generation_id=uuid.uuid4(),
        set_id=uuid.uuid4(),
    )
    company = Company(id=COMPANY_ID, name="My company", created_at=datetime.now(UTC))
    company.members = [
        Member(
            company_id=COMPANY_ID,
            user_id="bob",
            invited_email="bob@example.com",
            role=role,
            created_at=datetime.now(UTC),
        )
    ]

    return interview, company


def test_only_owner_or_admin_can_regenerate(client, monkeypatch, audited):
    sign_in()
    calls = []

    async def fake_regenerate(question_id, set_id, user_id, paid):
        calls.append((user_id, paid))

        return httpx.Response(200, json={"id": str(QUESTION_ID), "text": "New question?"})

    async def has_paid(_company_id):
        return True

    monkeypatch.setattr(generation, "regenerate_question", fake_regenerate)
    # Whether the company ever paid goes along: a paying one isn't held to the daily limit.
    monkeypatch.setattr(billing, "company_paid", has_paid)
    url = f"/interviews/{INTERVIEW_ID}/questions/{QUESTION_ID}/regenerate"

    for role, expected in (("viewer", 403), ("admin", 200), ("owner", 200)):
        interview, company = interview_and_company(role)

        async def fake_interview(session, _interview_id, interview=interview):
            return interview

        async def fake_company(session, _company_id, company=company):
            return company

        monkeypatch.setattr(interviews, "get", fake_interview)
        monkeypatch.setattr(companies, "get", fake_company)

        assert client.post(url).status_code == expected

    assert calls == [("bob", True), ("bob", True)]
    assert [event[1:] for event in audited] == [
        ("bob", AuditAction.QUESTIONS_REGENERATED, INTERVIEW_ID, TargetKind.INTERVIEW)
    ] * 2

    app.dependency_overrides.clear()


def test_only_owner_or_admin_reads_reports(client, monkeypatch):
    sign_in()

    async def fake_reports(_set_id, _question_id, page):
        return [
            {
                "id": str(uuid.uuid4()),
                "reason": "unclear",
                "comment": "",
                "created_at": datetime.now(UTC).isoformat(),
            }
        ]

    monkeypatch.setattr(library, "get_question_reports", fake_reports)
    url = f"/interviews/{INTERVIEW_ID}/questions/{QUESTION_ID}/reports"

    for role, expected in (("viewer", 403), ("admin", 200)):
        interview, company = interview_and_company(role)

        async def fake_interview(session, _interview_id, interview=interview):
            return interview

        async def fake_company(session, _company_id, company=company):
            return company

        monkeypatch.setattr(interviews, "get", fake_interview)
        monkeypatch.setattr(companies, "get", fake_company)

        assert client.get(url).status_code == expected

    app.dependency_overrides.clear()


def test_topic_questions_come_with_their_options(client, monkeypatch):
    sign_in()
    interview = Interview(
        id=INTERVIEW_ID,
        company_id=COMPANY_ID,
        generation_id=uuid.uuid4(),
        set_id=uuid.uuid4(),
    )
    company = Company(id=COMPANY_ID, name="My company", created_at=datetime.now(UTC))
    company.members = [
        Member(
            company_id=COMPANY_ID,
            user_id="bob",
            invited_email="bob@example.com",
            role="owner",
            created_at=datetime.now(UTC),
        )
    ]

    async def fake_interview(session, _interview_id):
        return interview

    async def fake_company(session, _company_id):
        return company

    # A multi-answer question: two right options.
    question = {
        "id": str(QUESTION_ID),
        "text": "Explain indexes.",
        "options": [
            {"answer": "Faster reads", "correct": True},
            {"answer": "Slower writes", "correct": True},
        ],
        "multi": True,
        "likes": 3,
        "dislikes": 1,
        "reports": 0,
    }

    async def fake_questions(set_id, _topic_id):
        assert set_id == interview.set_id

        return [question]

    monkeypatch.setattr(interviews, "get", fake_interview)
    monkeypatch.setattr(companies, "get", fake_company)
    monkeypatch.setattr(library, "get_topic_questions", fake_questions)

    response = client.get(f"/interviews/{INTERVIEW_ID}/topics/{TOPIC_ID}/questions")

    assert response.status_code == 200
    assert response.json() == [question]

    app.dependency_overrides.clear()


def test_a_manager_marks_a_questions_answer_wrong_in_one_click(client, monkeypatch, audited):
    sign_in()
    marked = []

    async def context(_question_id, set_id=None):
        return {"set_id": str(set_id)}

    async def mark_wrong(question_id):
        marked.append(question_id)

    monkeypatch.setattr(library, "mark_wrong", mark_wrong)
    monkeypatch.setattr(question_routes, "get_redis", lambda: FakeRedis())
    url = f"/interviews/{INTERVIEW_ID}/questions/{QUESTION_ID}/wrong"

    for role, expected in (("viewer", 403), ("admin", 204)):
        interview, company = interview_and_company(role)

        async def fake_interview(session, _interview_id, interview=interview):
            return interview

        async def fake_company(session, _company_id, company=company):
            return company

        async def fake_context(question_id, interview=interview):
            return await context(question_id, interview.set_id)

        monkeypatch.setattr(interviews, "get", fake_interview)
        monkeypatch.setattr(companies, "get", fake_company)
        monkeypatch.setattr(library, "get_question_context", fake_context)

        assert client.post(url).status_code == expected

    assert marked == [QUESTION_ID]
    assert [event[1:] for event in audited] == [
        ("bob", AuditAction.ANSWER_KEY_REPORTED, INTERVIEW_ID, TargetKind.INTERVIEW)
    ]

    # A question from someone else's test isn't found.
    async def elsewhere(_question_id):
        return {"set_id": str(uuid.uuid4())}

    monkeypatch.setattr(library, "get_question_context", elsewhere)

    assert client.post(url).status_code == 404

    app.dependency_overrides.clear()


def test_marks_past_the_companys_daily_limit_are_refused_before_the_verifier(
    client, monkeypatch, audited
):
    sign_in()
    marked = []
    interview, company = interview_and_company("admin")
    redis = FakeRedis({"WRONG_MARKS_PER_COMPANY_DAY": 1})

    async def fake_interview(session, _interview_id):
        return interview

    async def fake_company(session, _company_id):
        return company

    async def fake_context(_question_id):
        return {"set_id": str(interview.set_id)}

    async def mark_wrong(question_id):
        marked.append(question_id)

    monkeypatch.setattr(interviews, "get", fake_interview)
    monkeypatch.setattr(companies, "get", fake_company)
    monkeypatch.setattr(library, "get_question_context", fake_context)
    monkeypatch.setattr(library, "mark_wrong", mark_wrong)
    monkeypatch.setattr(question_routes, "get_redis", lambda: redis)
    url = f"/interviews/{INTERVIEW_ID}/questions/{QUESTION_ID}/wrong"

    assert [client.post(url).status_code for _ in range(2)] == [204, 429]
    assert marked == [QUESTION_ID]

    app.dependency_overrides.clear()
