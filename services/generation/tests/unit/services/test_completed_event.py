import asyncio
import uuid
from types import SimpleNamespace

import pytest

from generation.integrations import library
from generation.models.generation import Generation
from generation.repositories import generations
from generation.services import outbox as outbox_service
from generation.services import pipeline
from generation.services.pipeline import stream_graph

SET_ID = uuid.uuid4()
COMPANY_ID = uuid.uuid4()


class FinishedGraph:
    """A graph whose run already finished: no more updates, just the final state."""

    async def astream(self, graph_input, config, stream_mode):
        return
        yield

    async def aget_state(self, config):
        return SimpleNamespace(
            values={
                "title": "Bookkeeper interview",
                "level": "basic",
                "requirements": [],
                "final": [],
            }
        )


@pytest.fixture
def published(monkeypatch):
    """Events the pipeline saves with the generation's last update (the outbox)."""
    sent = []

    async def saved(_payload):
        return SET_ID

    async def update(session, generation_id, event=None, **values):
        if event:
            sent.append(event)

        return True

    async def nothing():
        return None

    async def nothing_for(_set_id):
        return None

    async def not_cancelled(session, _generation_id):
        return False

    monkeypatch.setattr(outbox_service, "flush_quietly", nothing)
    monkeypatch.setattr(library, "create_interview", saved)
    monkeypatch.setattr(library, "create_template", saved)
    monkeypatch.setattr(generations, "update", update)
    monkeypatch.setattr(generations, "is_cancelled", not_cancelled)
    monkeypatch.setattr(pipeline, "check_sample", nothing_for)

    return sent


def run(kind="interview"):
    generation = Generation(
        id=uuid.uuid4(),
        kind=kind,
        owner_uid="alice",
        company_id=COMPANY_ID,
        text="Job description",
        progress=None,
    )
    asyncio.run(stream_graph(FinishedGraph(), generation, None, {}, 10))

    return generation


def test_finished_interview_is_announced_to_companies(published):
    generation = run()

    assert published == [
        (
            "generation.completed",
            {
                "generation_id": str(generation.id),
                "company_id": str(COMPANY_ID),
                "set_id": str(SET_ID),
                "title": "Bookkeeper interview",
                # Companies gives the test this level's seconds a question.
                "level": "basic",
            },
        )
    ]


def test_a_finished_template_is_saved_without_telling_companies(published):
    run("template")

    assert published == []


def test_a_set_saved_after_a_cancel_is_deleted(published, monkeypatch):
    deleted = []

    async def cancelled(session, generation_id, event=None, **values):
        return False

    async def delete_set(set_id):
        deleted.append(set_id)

    monkeypatch.setattr(generations, "update", cancelled)
    monkeypatch.setattr(library, "delete_set", delete_set)

    run()

    assert deleted == [SET_ID]


@pytest.mark.parametrize(("edited", "at_once"), [({}, 24), ({"GENERATION_CALLS_AT_ONCE": 6}, 6)])
def test_a_run_makes_as_many_ai_calls_at_once_as_set_in_controls(
    monkeypatch, redis, edited, at_once
):
    configs = []
    redis.limits.update({name: str(value) for name, value in edited.items()})

    class NewGraph:
        async def aget_state(self, config):
            return SimpleNamespace(values={})

    async def stream(graph, generation, graph_input, config, size):
        configs.append(config)

    async def not_cancelled(session, _generation_id):
        return False

    monkeypatch.setattr(pipeline, "stream_graph", stream)
    monkeypatch.setattr(generations, "is_cancelled", not_cancelled)
    generation = Generation(
        id=uuid.uuid4(), kind="interview", owner_uid="alice", company_id=COMPANY_ID, text="Job"
    )

    asyncio.run(pipeline.run_pipeline(NewGraph(), generation, None))

    assert configs[0]["max_concurrency"] == at_once


@pytest.mark.parametrize(
    ("kind", "edited", "size"),
    [
        ("interview", {}, 70),
        ("template", {}, 90),
        ("interview", {"INTERVIEW_QUESTIONS_PER_TOPIC": 40}, 40),
        ("template", {"TEMPLATE_QUESTIONS_PER_TOPIC": 120}, 120),
    ],
)
def test_a_new_run_takes_its_questions_per_topic_from_controls(
    monkeypatch, redis, kind, edited, size
):
    started = []
    redis.limits.update({name: str(value) for name, value in edited.items()})

    class NewGraph:
        async def aget_state(self, config):
            return SimpleNamespace(values={})

    async def stream(graph, generation, graph_input, config, size):
        started.append((graph_input["topic_size"], size))

    async def not_cancelled(session, _generation_id):
        return False

    monkeypatch.setattr(pipeline, "stream_graph", stream)
    monkeypatch.setattr(generations, "is_cancelled", not_cancelled)
    generation = Generation(
        id=uuid.uuid4(), kind=kind, owner_uid="alice", company_id=COMPANY_ID, text="Job"
    )

    asyncio.run(pipeline.run_pipeline(NewGraph(), generation, None))

    assert started == [(size, size)]


def test_a_continued_run_keeps_the_size_it_started_with(monkeypatch, redis):
    sizes = []
    redis.limits["INTERVIEW_QUESTIONS_PER_TOPIC"] = "40"

    class StartedGraph:
        async def aget_state(self, config):
            return SimpleNamespace(values={"input_text": "Job", "topic_size": 25})

    async def stream(graph, generation, graph_input, config, size):
        sizes.append((graph_input, size))

    async def not_cancelled(session, _generation_id):
        return False

    monkeypatch.setattr(pipeline, "stream_graph", stream)
    monkeypatch.setattr(generations, "is_cancelled", not_cancelled)
    generation = Generation(
        id=uuid.uuid4(), kind="interview", owner_uid="alice", company_id=COMPANY_ID, text="Job"
    )

    asyncio.run(pipeline.run_pipeline(StartedGraph(), generation, None))

    assert sizes == [(None, 25)]
