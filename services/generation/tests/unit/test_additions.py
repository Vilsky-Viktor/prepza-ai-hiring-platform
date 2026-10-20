import asyncio
import uuid

import pytest
from prepza_common.auth import current_user
from prepza_common.sets import AdditionContext, AdditionTopic, QuestionIn
from prepza_common.user import User

from app.constants.additions import ADDED_QUESTIONS_INVALID, ADDITION_RUNNING, NOTHING_TO_TOP_UP
from app.helpers.additions import planned
from app.integrations import library
from app.main import app
from app.models.generation import Generation
from app.services import additions, jobs
from app.services.nodes.fill import TopicShortError
from app.storage import generations
from tests.unit.fakes import OPTIONS

TEMPLATE_ID = uuid.uuid4()


def topic(title="Ledgers", practice_missing=0, company_missing=0, texts=()):
    return AdditionTopic(
        id=uuid.uuid4(),
        title=title,
        subtopics=["Accruals", "Payroll"],
        texts=list(texts),
        practice_missing=practice_missing,
        company_missing=company_missing,
    )


def context(*topics):
    return AdditionContext(level="mid", language="en", topics=list(topics))


def test_a_top_up_writes_what_a_topic_lacks_and_an_addition_a_third_for_practice():
    short = topic(practice_missing=4, company_missing=0)

    assert planned(short, None) == (4, 0)
    assert planned(short, 30) == (10, 20)
    assert planned(short, 90) == (30, 60)


@pytest.fixture
def superadmin(monkeypatch):
    """Ann, the only superadmin; library knows one template, and additions are recorded."""
    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")
    app.dependency_overrides[current_user] = lambda: User(
        uid="u1",
        email="ann@example.com",
        email_verified=True,
        sign_in_provider="google.com",
    )
    state = {"context": context(topic(practice_missing=2)), "running": False, "created": []}

    async def get_addition_context(template_id):
        return state["context"] if template_id == TEMPLATE_ID else None

    async def create_addition(owner_uid, template_id, language, question_count):
        if state["running"]:
            return None

        row = Generation(
            id=uuid.uuid4(),
            kind="template_questions",
            status="queued",
            preparation_id=template_id,
            question_count=question_count,
        )
        state["created"].append(row)

        return row

    monkeypatch.setattr(library, "get_addition_context", get_addition_context)
    monkeypatch.setattr(generations, "create_addition", create_addition)

    yield state

    app.dependency_overrides.clear()


def test_a_superadmin_tops_up_a_short_template_once_at_a_time(client, superadmin, queued):
    started = client.post(f"/superadmin/templates/{TEMPLATE_ID}/top-up")
    superadmin["running"] = True
    again = client.post(f"/superadmin/templates/{TEMPLATE_ID}/top-up")

    assert started.status_code == 201
    assert started.json()["status"] == "queued"
    assert [row.question_count for row in superadmin["created"]] == [None]
    assert queued == [("/internal/jobs/run-generation", {"generation_id": started.json()["id"]})]
    assert again.status_code == 409
    assert again.json()["detail"] == ADDITION_RUNNING


def test_a_template_with_nothing_missing_has_nothing_to_top_up(client, superadmin):
    superadmin["context"] = context(topic())

    refused = client.post(f"/superadmin/templates/{TEMPLATE_ID}/top-up")
    added = client.post(f"/superadmin/templates/{TEMPLATE_ID}/additions", json={"count": 30})

    assert refused.status_code == 409
    assert refused.json()["detail"] == NOTHING_TO_TOP_UP
    assert added.status_code == 201
    assert [row.question_count for row in superadmin["created"]] == [30]


@pytest.mark.parametrize("count", [0, 31, 93, -3])
def test_an_addition_is_from_3_to_90_questions_in_steps_of_3(client, superadmin, count):
    refused = client.post(f"/superadmin/templates/{TEMPLATE_ID}/additions", json={"count": count})

    assert refused.status_code == 422
    assert refused.json()["detail"][0]["msg"] == f"Value error, {ADDED_QUESTIONS_INVALID}"
    assert superadmin["created"] == []


def test_an_unknown_template_gets_no_addition(client, superadmin):
    response = client.post(f"/superadmin/templates/{uuid.uuid4()}/top-up")

    assert response.status_code == 404
    assert response.json()["detail"] == "Template not found"


def test_the_page_reads_the_latest_addition_and_the_numbers_it_may_ask_for(
    client, superadmin, monkeypatch
):
    latest = {}

    async def latest_addition(template_id):
        return latest.get(template_id)

    monkeypatch.setattr(generations, "latest_addition", latest_addition)
    none = client.get(f"/superadmin/templates/{TEMPLATE_ID}/additions/latest").json()
    latest[TEMPLATE_ID] = Generation(
        id=uuid.uuid4(),
        status="running",
        progress={"done": 3, "total": 8, "topics": 2, "topics_ready": 1},
        error=None,
    )
    running = client.get(f"/superadmin/templates/{TEMPLATE_ID}/additions/latest").json()

    assert none["status"] is None
    assert (none["default_count"], none["count_step"], none["max_count"]) == (30, 3, 90)
    assert running["status"] == "running"
    assert running["progress"]["done"] == 3


def test_anyone_else_cant_add_questions(client, superadmin):
    app.dependency_overrides[current_user] = lambda: User(
        uid="u2",
        email="eve@example.com",
        email_verified=True,
        sign_in_provider="google.com",
    )

    assert client.post(f"/superadmin/templates/{TEMPLATE_ID}/top-up").status_code == 404
    assert superadmin["created"] == []


def run_addition(monkeypatch, found, count):
    async def get_addition_context(template_id):
        return found

    monkeypatch.setattr(library, "get_addition_context", get_addition_context)
    generation = Generation(
        id=uuid.uuid4(),
        kind="template_questions",
        preparation_id=TEMPLATE_ID,
        question_count=count,
    )

    asyncio.run(additions.run_addition(generation))


def test_an_addition_writes_practice_fresh_and_takes_at_most_half_the_company_side_from_the_bank(
    monkeypatch, writer
):
    writer["bank"] = [
        QuestionIn(text=f"Bank {index}?", options=OPTIONS, source_id=uuid.uuid4())
        for index in range(30)
    ] + [QuestionIn(text="Already here?", options=OPTIONS, source_id=uuid.uuid4())]
    found = context(topic(texts=["Already here?"]), topic("Payroll"))

    run_addition(monkeypatch, found, 30)

    [saved] = writer["saved"]
    first, second = saved.topics

    assert [len(first.practice), len(first.company)] == [10, 20]
    assert not any(question.source_id for question in first.practice)
    assert sum(question.source_id is not None for question in first.company) == 10
    # A bank question goes into one topic only.
    assert not any(question.source_id for question in second.company)
    assert [len(second.practice), len(second.company)] == [10, 20]
    assert writer["updates"][-1] == {"status": "done"}


def test_a_top_up_writes_only_what_short_topics_lack(monkeypatch, writer):
    found = context(topic(practice_missing=3), topic("Payroll"), topic("Tax", company_missing=1))

    run_addition(monkeypatch, found, None)

    [saved] = writer["saved"]

    assert [(len(t.practice), len(t.company)) for t in saved.topics] == [(3, 0), (0, 1)]
    assert [t.topic_id for t in saved.topics] == [found.topics[0].id, found.topics[2].id]


def test_a_topic_left_short_fails_the_run_and_saves_nothing(monkeypatch, writer):
    writer["short"] = True

    with pytest.raises(TopicShortError):
        run_addition(monkeypatch, context(topic(practice_missing=3)), None)

    assert writer["saved"] == []


def test_the_job_runs_an_addition_without_the_graph(monkeypatch):
    ran = []
    generation = Generation(id=uuid.uuid4(), kind="template_questions")

    async def claim_run(generation_id):
        return True

    async def get(generation_id):
        return generation

    async def run_addition(row):
        ran.append(row.id)

    monkeypatch.setattr(generations, "claim_run", claim_run)
    monkeypatch.setattr(generations, "get", get)
    monkeypatch.setattr(jobs, "run_addition", run_addition)

    asyncio.run(jobs.run_generation(None, generation.id, None))

    assert ran == [generation.id]
