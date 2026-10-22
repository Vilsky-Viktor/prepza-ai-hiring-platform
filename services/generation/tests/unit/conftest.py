import base64
import itertools
import json
import uuid

import pytest
from fake_redis import FakeRedis
from prepza_common import memory_cache, pubsub

from app.integrations import library, llm
from app.routers import internal, superadmin, superadmin_additions
from app.services import (
    additions,
    budget,
    key_self_check,
    pipeline,
    review,
    sample_checks,
    top_up,
    topic_caps,
    translations,
)
from app.services.nodes import reuse
from app.storage import generations
from tests.unit.fakes import EXAMPLE, MULTI_OPTIONS, OPTIONS


@pytest.fixture(autouse=True)
def no_langfuse(monkeypatch):
    """No test traces to Langfuse, also when its keys are set where tests run."""
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)


@pytest.fixture(autouse=True)
def redis(monkeypatch):
    """Redis in memory for the requests' limits and budgets: unit tests have none. Each test
    reads the limits afresh, not values an earlier test cached."""
    fake = FakeRedis()
    monkeypatch.setattr(memory_cache, "_entries", {})

    for module in (
        internal,
        superadmin,
        superadmin_additions,
        budget,
        review,
        additions,
        reuse,
        pipeline,
        topic_caps,
        translations,
        sample_checks,
        key_self_check,
    ):
        monkeypatch.setattr(module, "get_redis", lambda: fake)

    return fake


@pytest.fixture(autouse=True)
def events(monkeypatch):
    """The events published straight to Pub/Sub (AI used, limit hit), as (type, data); none
    reaches it."""
    sent = []

    async def publish_batch(messages, timeout=None):
        for message in messages:
            data = json.loads(base64.b64decode(message["data"]))
            sent.append((message["attributes"]["type"], data))

    monkeypatch.setattr(pubsub, "publish_batch", publish_batch)

    return sent


class Embeddings:
    async def aembed_documents(self, texts):
        return [[1.0] for _ in texts]


@pytest.fixture
def writer(monkeypatch):
    """Questions written as asked, every one distinct, none when `short`, never multi-answer
    when `no_multi`, the pipeline's calls without examples when `no_examples`; the bank offers what `bank` holds; the calls' tasks, what library saved and
    the generation's updates are recorded."""
    counter = itertools.count()
    recorded = {"bank": [], "saved": [], "updates": [], "tasks": [], "fills": [], "short": False}
    recorded["no_multi"] = False
    recorded["no_examples"] = False

    def written(count, multi, examples=0):
        # The first `multi` are multi-answer, the last `examples` have an example.
        return [
            {
                "text": f"New {next(counter)}?" + (EXAMPLE if i >= count - examples else ""),
                "options": MULTI_OPTIONS if i < multi else OPTIONS,
            }
            for i in range(0 if recorded["short"] else count)
        ]

    async def generate_questions(task):
        recorded["tasks"].append(task)
        multi = 0 if recorded["no_multi"] else task["multi"]
        examples = 0 if recorded["no_examples"] else task.get("examples", 0)

        return {"question_pool": [{"questions": written(task["count"], multi, examples)}]}

    async def distinct_by_meaning(texts, keep_first=0):
        return list(range(len(texts)))

    async def new_questions(item, missing, state, multi=False, example=False):
        recorded["fills"].append((multi, example, missing))

        if multi and recorded["no_multi"]:
            return []

        return written(missing, missing if multi else 0, missing if example else 0)

    async def find_reusable(request):
        return recorded["bank"][: request.count]

    async def add_questions(template_id, added):
        recorded["saved"].append(added)

        return [[uuid.uuid4()] for _ in added.topics]

    async def update(generation_id, event=None, **values):
        recorded["updates"].append(values)

        return True

    async def check_topics(ids):
        return None

    monkeypatch.setattr(additions, "generate_questions", generate_questions)
    monkeypatch.setattr(additions, "distinct_by_meaning", distinct_by_meaning)
    monkeypatch.setattr(top_up, "new_questions", new_questions)
    monkeypatch.setattr(additions, "check_topics", check_topics)
    monkeypatch.setattr(llm, "get_embeddings", lambda: Embeddings())
    monkeypatch.setattr(library, "find_reusable", find_reusable)
    monkeypatch.setattr(library, "add_questions", add_questions)
    monkeypatch.setattr(generations, "update", update)

    return recorded
