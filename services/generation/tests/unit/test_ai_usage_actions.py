import asyncio
import uuid
from types import SimpleNamespace

import pytest
from prepza_common.ai_constants import AI_USED
from prepza_common.auth import current_user
from prepza_common.user import User

from app.constants.actions import (
    CAMPAIGN_TRANSLATION,
    CODE_TAGS,
    EMBEDDINGS,
    INTERVIEW_GENERATION,
    NEWS_TRANSLATION,
    QUESTION_REGENERATION,
    QUESTION_VERIFY,
    SAMPLE_KEY_CHECK,
    TEMPLATE_GENERATION,
    TEMPLATE_QUESTION_REGENERATION,
)
from app.constants.quality import QualityFlag
from app.integrations import library, llm, notifications
from app.jobs import tag_code_languages as tag_job
from app.jobs.embed_templates import embed_templates
from app.main import app
from app.models.generation import Generation
from app.schemas.campaigns import CampaignSource
from app.schemas.news import NewsSource
from app.schemas.regenerate import QuestionContext
from app.services import campaigns, news, pipeline, sample_checks
from app.services import regenerate as regenerate_module
from app.services import verify as verify_service
from app.storage import generations
from tests.unit.fake_ai import HANG, Chat, reply
from tests.unit.test_internal_generations import headers
from tests.unit.test_verify import question

COMPANY_ID = uuid.uuid4()
QUESTION_ID = uuid.uuid4()


def recorded(events):
    """Each recorded call's action, company, user and outcome."""
    return [
        (data["action"], data["company_id"], data["user_id"], data["outcome"])
        for kind, data in events
        if kind == AI_USED
    ]


class Graph:
    """A pipeline that makes one model call and pauses for the topics' review."""

    def __init__(self):
        self.chat = Chat(replies=[reply(100, 10)])

    async def aget_state(self, config):
        return SimpleNamespace(values={})

    async def astream(self, graph_input, config, stream_mode):
        await self.chat.ainvoke("Draft the topics")

        yield {"__interrupt__": [SimpleNamespace(value={"topics": []})]}


@pytest.mark.parametrize(
    "kind, company_id, action, cancelled, outcome",
    [
        ("interview", COMPANY_ID, INTERVIEW_GENERATION, False, "ok"),
        ("template", None, TEMPLATE_GENERATION, False, "ok"),
        ("interview", COMPANY_ID, INTERVIEW_GENERATION, True, "cut"),
    ],
)
def test_a_generation_run_is_recorded_for_its_kind_company_and_owner(
    events, monkeypatch, kind, company_id, action, cancelled, outcome
):
    async def is_cancelled(generation_id):
        return cancelled

    async def update(generation_id, event=None, **values):
        return True

    monkeypatch.setattr(generations, "is_cancelled", is_cancelled)
    monkeypatch.setattr(generations, "update", update)
    generation = Generation(
        id=uuid.uuid4(), kind=kind, company_id=company_id, owner_uid="bob", text="Accountant"
    )

    asyncio.run(pipeline.run_pipeline(Graph(), generation, None))

    company = str(company_id) if company_id else None
    assert recorded(events) == [(action, company, "bob", outcome)]


def question_context(kind="interview"):
    return QuestionContext(
        set_id=uuid.uuid4(),
        kind=kind,
        owner_id=str(COMPANY_ID) if kind == "interview" else "ann",
        level="mid",
        topic="Python",
        subtopics=[],
        existing=[],
    )


def written_by(chat):
    async def write(context, reasons):
        await chat.ainvoke("Write a question")

        return "New question?", []

    return write


def test_a_regenerated_question_is_recorded_for_its_company_and_user(client, events, monkeypatch):
    found = question_context()

    async def context(question_id):
        return found

    async def replace(question_id, question):
        pass

    monkeypatch.setattr(library, "get_question_context", context)
    monkeypatch.setattr(library, "replace_question", replace)
    monkeypatch.setattr(regenerate_module, "write", written_by(Chat(replies=[reply(100, 10)])))

    response = client.post(
        f"/internal/questions/{QUESTION_ID}/regenerate",
        json={"user_id": "bob", "set_id": str(found.set_id)},
        headers=headers(),
    )

    assert response.status_code == 200
    assert recorded(events) == [(QUESTION_REGENERATION, str(COMPANY_ID), "bob", "ok")]


def test_a_regeneration_out_of_time_is_recorded_cut(client, events, monkeypatch):
    found = question_context()

    async def context(question_id):
        return found

    monkeypatch.setattr(library, "get_question_context", context)
    monkeypatch.setattr(regenerate_module, "REGENERATE_TIMEOUT_SECONDS", 0.05)
    monkeypatch.setattr(regenerate_module, "write", written_by(Chat(replies=[HANG])))

    response = client.post(
        f"/internal/questions/{QUESTION_ID}/regenerate",
        json={"user_id": "bob", "set_id": str(found.set_id)},
        headers=headers(),
    )

    assert response.status_code == 502
    assert recorded(events) == [(QUESTION_REGENERATION, str(COMPANY_ID), "bob", "cut")]


def test_a_regenerated_template_question_is_the_superadmins(client, events, monkeypatch):
    found = question_context("template")

    async def context(question_id):
        return found

    async def replace(question_id, question):
        pass

    monkeypatch.setenv("SUPERADMIN_EMAILS", "ann@example.com")
    app.dependency_overrides[current_user] = lambda: User(
        uid="ann",
        email="ann@example.com",
        email_verified=True,
        sign_in_provider="google.com",
    )
    monkeypatch.setattr(library, "get_question_context", context)
    monkeypatch.setattr(library, "replace_question", replace)
    monkeypatch.setattr(regenerate_module, "write", written_by(Chat(replies=[reply(100, 10)])))

    try:
        response = client.post(
            f"/superadmin/templates/{found.set_id}/questions/{QUESTION_ID}/regenerate"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert recorded(events) == [(TEMPLATE_QUESTION_REGENERATION, None, "ann", "ok")]


def test_a_flagged_questions_check_and_a_sample_key_check_are_recorded(events, monkeypatch):
    chat = Chat(replies=[reply(100, 10), reply(100, 10)])
    flagged = question().model_copy(update={"flag": QualityFlag.REWRITE})

    async def context(question_id):
        return question_context()

    async def quality(question_id):
        return flagged

    async def called(*args):
        await chat.ainvoke("Check the question")

    monkeypatch.setattr(library, "get_question_context", context)
    monkeypatch.setattr(library, "get_question_quality", quality)
    monkeypatch.setattr(verify_service, "replace", called)
    monkeypatch.setattr(sample_checks, "check_key", called)

    asyncio.run(verify_service.verify(QUESTION_ID, QualityFlag.REWRITE))
    asyncio.run(sample_checks.check_one(QUESTION_ID))

    # The flag's check is prepza's own work; a new test's sample is its company's.
    assert recorded(events) == [
        (QUESTION_VERIFY, None, None, "ok"),
        (SAMPLE_KEY_CHECK, str(COMPANY_ID), None, "ok"),
    ]


def test_news_and_campaign_translations_are_recorded(events, monkeypatch):
    chat = Chat(replies=[reply(100, 10), reply(100, 10)])

    async def translated(source, language):
        await chat.ainvoke("Translate")

        return source

    async def news_source(news_id):
        return NewsSource(title="News", text="Text", missing=["de"])

    async def campaign_source(campaign_id):
        return CampaignSource(subject="News", text="Text", button=None, missing=["de"])

    async def saved(*args):
        pass

    monkeypatch.setattr(library, "get_news_source", news_source)
    monkeypatch.setattr(library, "save_news_translations", saved)
    monkeypatch.setattr(notifications, "get_campaign_source", campaign_source)
    monkeypatch.setattr(notifications, "save_campaign_translations", saved)
    monkeypatch.setattr(news, "translate_one", translated)
    monkeypatch.setattr(campaigns, "translate_one", translated)

    asyncio.run(news.translate_news(uuid.uuid4()))
    asyncio.run(campaigns.translate_campaign(uuid.uuid4()))

    assert recorded(events) == [
        (NEWS_TRANSLATION, None, None, "ok"),
        (CAMPAIGN_TRANSLATION, None, None, "ok"),
    ]


def test_tagging_examples_notation_is_recorded(events, monkeypatch):
    chat = Chat(replies=[reply(100, 10)])
    pages = [[{"id": "q1", "text": "Q?\n```\nprint(1)\n```"}], []]

    async def untagged_code(limit, text=False, after=None):
        return pages.pop(0)

    async def tagged(examples):
        await chat.ainvoke("Tag")

        return {0: "python"}

    async def saved(*args):
        pass

    monkeypatch.setattr(library, "untagged_code", untagged_code)
    monkeypatch.setattr(library, "save_code_languages", saved)
    monkeypatch.setattr(tag_job, "tag_examples", tagged)

    assert asyncio.run(tag_job.tag_code_languages()) == 1
    assert recorded(events) == [(CODE_TAGS, None, None, "ok")]


def test_embedding_templates_topics_is_recorded(events, monkeypatch):
    batches = [[{"id": "t1", "title": "Python", "subtopics": ["asyncio"]}], []]

    class Embeddings:
        async def aembed_documents(self, texts):
            return [[1.0] for _ in texts]

    async def missing(size):
        return batches.pop(0)

    async def saved(vectors):
        pass

    monkeypatch.setattr(llm, "get_embeddings", lambda: Embeddings())
    monkeypatch.setattr(library, "missing_embeddings", missing)
    monkeypatch.setattr(library, "save_embeddings", saved)

    assert asyncio.run(embed_templates()) == 1
    assert recorded(events) == [(EMBEDDINGS, None, None, "ok")]
