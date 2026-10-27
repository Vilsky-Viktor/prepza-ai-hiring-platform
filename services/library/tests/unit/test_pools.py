import uuid
from types import SimpleNamespace

import pytest
from prepza_common.ai.multi_answer import multi_count
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User
from prepza_common.http.http import bearer

from app.helpers.pools import assign_pools, missing
from app.main import app
from app.storage import pools, preparations
from tests.unit.test_internal import token
from tests.unit.test_superadmin_templates import TEMPLATE

OPTIONS = [{"answer": "a", "correct": True}, {"answer": "b", "correct": False}]
MULTI_OPTIONS = [
    {"answer": "a", "correct": True},
    {"answer": "b", "correct": True},
    {"answer": "c", "correct": False},
    {"answer": "d", "correct": False},
]


EXAMPLE = "What does it print?\n```python\nprint(1)\n```"


def fresh(count, multi=False, example=False):
    return [
        SimpleNamespace(
            id=uuid.uuid4(),
            source_question_id=None,
            pool=None,
            text=EXAMPLE if example else "Why?",
            options=MULTI_OPTIONS if multi else OPTIONS,
        )
        for _ in range(count)
    ]


def reused(count, example=False):
    return [
        SimpleNamespace(
            id=uuid.uuid4(),
            source_question_id=uuid.uuid4(),
            pool=None,
            text=EXAMPLE if example else "Why?",
            options=OPTIONS,
        )
        for _ in range(count)
    ]


def test_a_new_template_topic_gives_30_fresh_questions_to_practice_and_the_rest_to_companies():
    bank = reused(45)
    new = fresh(45)
    assign_pools(bank + new, 0.1)

    assert {question.pool for question in bank} == {"company"}
    assert [question.pool for question in new] == ["practice"] * 30 + ["company"] * 15


def test_questions_reused_from_the_bank_are_company_only_wherever_they_stand():
    questions = fresh(10) + reused(5) + fresh(25)
    assign_pools(questions, 0.1)

    assert [question.pool for question in questions[10:15]] == ["company"] * 5
    assert sum(question.pool == "practice" for question in questions) == 30
    assert questions[-5].pool == "company"


def test_practice_takes_its_share_of_multi_answer_questions_wherever_they_stand():
    single = fresh(40)
    multi = fresh(10, multi=True)
    assign_pools(single + multi, 0.1)
    practice = [question for question in single + multi if question.pool == "practice"]

    # 30 practice questions, multi_count(30, 0.1) of them multi-answer; the rest go to companies.
    assert len(practice) == 30
    assert sum(question in multi for question in practice) == multi_count(30, 0.1)
    assert sum(question.pool == "company" for question in multi) == 10 - multi_count(30, 0.1)


def test_each_pool_takes_its_share_of_the_questions_with_an_example():
    # 33 of 90 have one: practice takes 11 of its 30, companies the other 22 of their 60.
    plain = fresh(57)
    shown = fresh(33, example=True)
    assign_pools(shown + plain, 0.1)

    assert sum(question.pool == "practice" for question in shown) == 11
    assert sum(question.pool == "practice" for question in plain + shown) == 30

    # Bank questions with an example count toward the topic's share but stay with companies.
    bank = reused(9, example=True)
    plain = fresh(54)
    shown = fresh(27, example=True)
    assign_pools(bank + plain + shown, 0.1)

    assert sum(question.pool == "practice" for question in shown) == 12
    assert {question.pool for question in bank} == {"company"}


def test_practice_makes_up_a_short_kind_with_the_other():
    single = fresh(40)
    multi = fresh(1, multi=True)
    assign_pools(multi + single, 0.1)

    assert multi[0].pool == "practice"
    assert sum(question.pool == "practice" for question in single) == 29

    only_multi = fresh(35, multi=True)
    assign_pools(only_multi, 0.1)

    assert sum(question.pool == "practice" for question in only_multi) == 30


def test_a_topic_lacks_what_falls_short_of_30_practice_and_60_company_questions():
    assert missing(30, 60) == (0, 0)
    assert missing(12, 70) == (18, 0)
    assert missing(40, 41) == (0, 19)


@pytest.fixture
def superadmin(monkeypatch):
    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")
    app.dependency_overrides[current_user] = lambda: User(
        uid="u1",
        email="ann@example.com",
        email_verified=True,
        sign_in_provider="google.com",
    )

    async def get(set_id):
        return TEMPLATE if set_id == TEMPLATE.id else SimpleNamespace(kind="interview")

    async def duplicate_ids(ids):
        return set()

    from app.storage import templates

    monkeypatch.setattr(preparations, "get", get)
    monkeypatch.setattr(templates, "duplicate_ids", duplicate_ids)

    yield

    app.dependency_overrides.clear()


def topic(title):
    return SimpleNamespace(id=uuid.uuid4(), title=title, subtopics=["Accruals"])


def test_the_superadmin_sees_each_topics_pools_and_whether_a_top_up_is_due(
    client, superadmin, monkeypatch
):
    counts = [(topic("Ledgers"), 30, 60), (topic("Payroll"), 30, 58)]

    async def topic_counts(template_id):
        return counts

    monkeypatch.setattr(pools, "topic_counts", topic_counts)

    found = client.get(f"/superadmin/templates/{TEMPLATE.id}").json()

    assert [(t["title"], t["practice_count"], t["company_count"]) for t in found["topics"]] == [
        ("Ledgers", 30, 60),
        ("Payroll", 30, 58),
    ]
    assert found["short"] is True

    counts[1] = (counts[1][0], 31, 90)

    assert client.get(f"/superadmin/templates/{TEMPLATE.id}").json()["short"] is False


def test_generation_gets_each_topics_texts_and_what_each_pool_lacks(
    client, superadmin, monkeypatch
):
    questions = [SimpleNamespace(text=f"Q{index}?", pool="practice") for index in range(25)] + [
        SimpleNamespace(text="Bank?", pool="company")
    ]
    ledgers = SimpleNamespace(**vars(topic("Ledgers")), questions=questions)

    async def topics_with_questions(template_id):
        return [ledgers]

    monkeypatch.setattr(pools, "topics_with_questions", topics_with_questions)
    headers = bearer(token())

    found = client.get(f"/internal/templates/{TEMPLATE.id}/additions", headers=headers).json()
    interview = client.get(f"/internal/templates/{uuid.uuid4()}/additions", headers=headers)

    assert (found["level"], found["language"]) == ("hard", "en")
    [only] = found["topics"]
    assert (only["practice_missing"], only["company_missing"]) == (5, 59)
    assert only["texts"][-1] == "Bank?" and len(only["texts"]) == 26
    assert interview.status_code == 404


def test_added_questions_are_saved_by_pool_and_never_into_another_templates_topic(
    client, superadmin, monkeypatch
):
    saved = []
    ids = [[uuid.uuid4()]]
    foreign_topic = uuid.uuid4()

    async def add_questions(template_id, added):
        saved.append((template_id, added))

        return None if added[0].topic_id == foreign_topic else ids

    monkeypatch.setattr(pools, "add_questions", add_questions)
    headers = bearer(token())

    def body(topic_id):
        return {
            "topics": [
                {
                    "topic_id": str(topic_id),
                    "practice": [{"text": "New?", "options": OPTIONS}],
                    "company": [],
                }
            ]
        }

    path = f"/internal/templates/{TEMPLATE.id}/questions"
    created = client.post(path, json=body(uuid.uuid4()), headers=headers)
    foreign = client.post(path, json=body(foreign_topic), headers=headers)

    assert created.status_code == 201
    assert created.json() == [[str(ids[0][0])]]
    assert saved[0][1][0].practice[0].text == "New?"
    assert foreign.status_code == 404
    assert foreign.json()["detail"] == "Topic not found"
