import uuid
from datetime import UTC, datetime

from testee_common.auth.auth import current_user
from testee_common.auth.user import User

from companies.constants.interviews import DEFAULT_TOPIC_QUESTIONS
from companies.helpers.interviews import pick_questions, session_topics, topics_out
from companies.integrations import library
from companies.main import app
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.repositories import companies, interviews

COMPANY_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()
TOPIC_ID = uuid.uuid4()
OTHER_ID = uuid.uuid4()


def setup(monkeypatch, saved, limits=None, topics=None):
    """An interview with `topics` (SQL, 10 questions, by default) at `limits`; the numbers a change
    saves go to `saved` and become the interview's."""
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True, name="Bob"
    )
    interview = Interview(
        id=INTERVIEW_ID,
        company_id=COMPANY_ID,
        generation_id=uuid.uuid4(),
        set_id=uuid.uuid4(),
        topic_limits=dict(limits or {}),
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

    async def fake_set(_set_id):
        return {"topics": topics or [{"id": str(TOPIC_ID), "title": "SQL", "question_count": 10}]}

    async def fake_save(session, _interview_id, change):
        interview.topic_limits = change(interview.topic_limits)
        saved.append(dict(interview.topic_limits))

    monkeypatch.setattr(interviews, "get", fake_interview)
    monkeypatch.setattr(companies, "get", fake_company)
    monkeypatch.setattr(library, "get_set", fake_set)
    monkeypatch.setattr(interviews, "set_topic_limits", fake_save)


def test_limit_cannot_exceed_topic_questions(client, monkeypatch):
    saved = []
    setup(monkeypatch, saved)
    url = f"/interviews/{INTERVIEW_ID}/topics/{TOPIC_ID}/limit"

    assert client.put(url, json={"limit": 11}).status_code == 422
    assert client.put(url, json={"limit": -1}).status_code == 422
    assert client.put(url, json={"limit": None}).status_code == 422
    assert client.put(url, json={"limit": 5}).status_code == 204
    # The whole topic: every candidate gets every question.
    assert client.put(url, json={"limit": 10}).status_code == 204
    assert saved == [{str(TOPIC_ID): 5}, {str(TOPIC_ID): 10}]

    app.dependency_overrides.clear()


def two_topics(size: int = 10):
    return [
        {"id": str(TOPIC_ID), "title": "SQL", "question_count": size},
        {"id": str(OTHER_ID), "title": "Git", "question_count": size},
    ]


def test_a_topic_can_be_set_to_0_questions_while_another_has_some(client, monkeypatch):
    saved = []
    setup(monkeypatch, saved, topics=two_topics())

    response = client.put(f"/interviews/{INTERVIEW_ID}/topics/{TOPIC_ID}/limit", json={"limit": 0})

    assert response.status_code == 204
    # The other topic keeps the number it had.
    assert saved == [{str(TOPIC_ID): 0, str(OTHER_ID): 10}]

    app.dependency_overrides.clear()


def test_the_last_topic_with_questions_cannot_be_set_to_0(client, monkeypatch):
    saved = []
    setup(monkeypatch, saved, limits={str(OTHER_ID): 0}, topics=two_topics())

    response = client.put(f"/interviews/{INTERVIEW_ID}/topics/{TOPIC_ID}/limit", json={"limit": 0})

    assert response.status_code == 422
    assert response.json()["detail"] == "An interview needs at least one topic with questions."
    assert saved == []

    app.dependency_overrides.clear()


def test_a_session_leaves_out_a_topic_set_to_0():
    interview = Interview(topic_limits={str(OTHER_ID): 0, str(TOPIC_ID): 2})
    options = [{"answer": "a", "correct": True}, {"answer": "b", "correct": False}]
    content = {
        "id": "preparation",
        "topics": [
            {
                "id": str(topic_id),
                "title": title,
                "questions": [{"id": i, "options": options} for i in range(5)],
            }
            for topic_id, title in ((TOPIC_ID, "SQL"), (OTHER_ID, "Git"))
        ],
    }

    topics = session_topics(interview, content, 0.1)

    assert [topic["title"] for topic in topics] == ["SQL"]
    assert len(topics[0]["questions"]) == 2


def test_unknown_topic_is_not_found(client, monkeypatch):
    setup(monkeypatch, [])
    url = f"/interviews/{INTERVIEW_ID}/topics/{uuid.uuid4()}/limit"

    assert client.put(url, json={"limit": 1}).status_code == 404

    app.dependency_overrides.clear()


def test_pick_questions_takes_a_random_subset():
    options = [{"answer": "a", "correct": True}, {"answer": "b", "correct": False}]
    questions = [{"id": index, "options": options} for index in range(100)]
    picked = [question["id"] for question in pick_questions(questions, 5, 0.1)]

    assert len(picked) == 5
    assert len(set(picked)) == 5
    assert set(picked) <= set(range(100))
    assert pick_questions(questions, 100, 0.1) == questions
    assert pick_questions(questions[:7], 10, 0.1) == questions[:7]


def test_a_topic_without_a_limit_asks_the_default_number():
    ids = [str(uuid.uuid4()) for _ in range(3)]
    found = {
        "topics": [
            {"id": ids[0], "title": "SQL", "question_count": 70},
            {"id": ids[1], "title": "Git", "question_count": 6},
            {"id": ids[2], "title": "APIs", "question_count": 70},
        ]
    }

    topics = topics_out(found, {ids[2]: 25})

    assert [topic.question_limit for topic in topics] == [DEFAULT_TOPIC_QUESTIONS, 6, 25]
    assert DEFAULT_TOPIC_QUESTIONS == 10


def ten_topics() -> list[dict]:
    return [
        {"id": str(topic_id), "title": f"Topic {index}", "question_count": 50}
        for index, topic_id in enumerate([TOPIC_ID, OTHER_ID, *(uuid.uuid4() for _ in range(8))])
    ]


def test_a_topic_raised_over_the_cap_is_refused_until_another_is_lowered(client, monkeypatch):
    """10 topics start at 6 questions each: 60, the cap."""
    saved = []
    setup(monkeypatch, saved, topics=ten_topics())
    url = f"/interviews/{INTERVIEW_ID}/topics/{{}}/limit"

    refused = client.put(url.format(TOPIC_ID), json={"limit": 7})
    lowered = client.put(url.format(OTHER_ID), json={"limit": 2})
    raised = client.put(url.format(TOPIC_ID), json={"limit": 10})

    assert refused.status_code == 422
    assert refused.json()["code"] == "too_many_questions"
    assert refused.json()["detail"] == "At most 60 questions per candidate; 0 left."
    assert (lowered.status_code, raised.status_code) == (204, 204)
    assert saved[-1][str(TOPIC_ID)] == 10
    assert sum(saved[-1].values()) == 60

    app.dependency_overrides.clear()


def test_an_interview_over_the_cap_may_only_come_down(client, monkeypatch):
    saved = []
    limits = {str(TOPIC_ID): 40, str(OTHER_ID): 40}
    setup(monkeypatch, saved, limits=limits, topics=two_topics(50))
    url = f"/interviews/{INTERVIEW_ID}/topics/{TOPIC_ID}/limit"

    refused = client.put(url, json={"limit": 41})
    lowered = client.put(url, json={"limit": 30})

    assert refused.json()["detail"] == "At most 60 questions per candidate; 0 left."
    assert lowered.status_code == 204
    assert saved == [{str(TOPIC_ID): 30, str(OTHER_ID): 40}]

    app.dependency_overrides.clear()
