"""The topic caps and questions per topic set in Controls, against the real database and Redis
(database 15): a value written to the hash billing keeps is what the next review and the next
run use."""

import uuid
from types import SimpleNamespace

import pytest
from testee_common.i18n.i18n import TemplateError
from testee_common.limits.limit_list import LIMITS_KEY
from testee_common.redis import memory_cache

from generation.constants.statuses import Status
from generation.integrations.redis import get_redis
from generation.repositories import generations
from generation.schemas.generation import ReviewRequest
from generation.services import pipeline
from generation.services.review import submit_review
from generation.services.topic_caps import generation_out
from tests.integration.transactions import transaction

# Values only generation reads, so no other service's tests in database 15 touch them.
NAMES = ("MAX_TOPICS", "MAX_SUBTOPICS", "INTERVIEW_QUESTIONS_PER_TOPIC")


@pytest.fixture
def controls(run):
    """Writes edited values to the limits' hash as billing does; removes them after."""
    memory_cache._entries.clear()

    def edit(**values):
        async def write():
            await get_redis().hset(LIMITS_KEY, mapping={k: str(v) for k, v in values.items()})

        run(write())
        get_redis.cache_clear()
        memory_cache._entries.clear()

    yield edit

    async def remove():
        await get_redis().hdel(LIMITS_KEY, *NAMES)

    run(remove())
    get_redis.cache_clear()
    memory_cache._entries.clear()


async def awaiting_review(count: int):
    created = await transaction(generations.create, f"ann-{uuid.uuid4().hex}", "Backend developer")
    topics = [{"main_topic": f"Topic {i}", "subtopics": []} for i in range(count)]
    await transaction(generations.update, created.id, status=Status.AWAITING_REVIEW, topics=topics)

    return await transaction(generations.get, created.id)


def test_a_review_is_held_to_the_caps_set_in_controls(run, controls):
    controls(MAX_TOPICS=3, MAX_SUBTOPICS=2)

    async def scenario():
        generation = await awaiting_review(5)
        shown = await generation_out(generation)
        refusals = []
        edited = {"main_topic": "Topic 0", "subtopics": ["A", "B", "C"]}

        for body in (
            ReviewRequest(selected=[0, 1, 2, 3]),
            ReviewRequest(selected=[0], topics=[edited]),
        ):
            with pytest.raises(TemplateError) as refused:
                await submit_review(generation, body)

            refusals.append(refused.value.detail)

        get_redis.cache_clear()

        return (shown.max_topics, shown.max_subtopics), refusals

    caps, refusals = run(scenario())

    assert caps == (3, 2)
    assert refusals == ["Choose at most 3 topics", "A topic can have at most 2 subtopics"]


def test_the_next_run_takes_its_questions_per_topic_from_controls(run, controls, monkeypatch):
    controls(INTERVIEW_QUESTIONS_PER_TOPIC=40)
    started = []

    class NewGraph:
        async def aget_state(self, config):
            return SimpleNamespace(values={})

    async def stream(graph, generation, graph_input, config, size):
        started.append((graph_input["topic_size"], size))

    monkeypatch.setattr(pipeline, "stream_graph", stream)

    async def scenario():
        generation = await transaction(
            generations.create, f"ann-{uuid.uuid4().hex}", "Backend developer"
        )
        await pipeline.run_pipeline(NewGraph(), generation, None)
        get_redis.cache_clear()

    run(scenario())

    assert started == [(40, 40)]


def test_without_an_edit_a_run_takes_the_default(run, controls, monkeypatch):
    started = []

    class NewGraph:
        async def aget_state(self, config):
            return SimpleNamespace(values={})

    async def stream(graph, generation, graph_input, config, size):
        started.append(size)

    monkeypatch.setattr(pipeline, "stream_graph", stream)

    async def scenario():
        generation = await transaction(
            generations.create, f"ann-{uuid.uuid4().hex}", "Backend developer"
        )
        await pipeline.run_pipeline(NewGraph(), generation, None)
        get_redis.cache_clear()

    run(scenario())

    assert started == [70]
