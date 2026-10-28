import asyncio
import uuid

from generation.helpers.payload import build_preparation
from generation.integrations import library, llm
from generation.schemas.questions import QuestionItemList
from generation.services.nodes.questions import generate_questions
from generation.services.nodes.reuse import find_reused


class Recorder:
    """Keeps the prompts it's sent and answers with no questions."""

    def __init__(self):
        self.prompts = []

    def with_structured_output(self, schema):
        return self

    async def ainvoke(self, messages):
        self.prompts.append(messages[-1].content)

        return QuestionItemList(items=[])

    async def aembed_documents(self, texts):
        return [[0.1] for _ in texts]


def test_questions_are_asked_for_in_the_users_language(monkeypatch):
    recorder = Recorder()
    monkeypatch.setattr(llm, "get_generation_llm", lambda *_: recorder)

    asyncio.run(
        generate_questions(
            {
                "topic_index": 0,
                "topic": "Bookkeeping",
                "subtopic_index": 0,
                "subtopic": "Journal entries",
                "count": 3,
                "level": "basic",
                "existing": [],
                "focus": "definitions",
                "language": "ru",
            }
        )
    )

    assert "Write 3 questions in Russian." in recorder.prompts[0]


def test_reuse_looks_only_at_sets_in_the_same_language(monkeypatch):
    asked = []

    async def fake_find(request):
        asked.append(request.language)

        return []

    monkeypatch.setattr(llm, "get_embeddings", lambda: Recorder())
    monkeypatch.setattr(library, "find_reusable", fake_find)

    asyncio.run(
        find_reused(
            {
                "topics": [{"main_topic": "Bookkeeping", "subtopics": []}],
                "level": "basic",
                "language": "ru",
            }
        )
    )

    assert asked == ["ru"]


def test_the_saved_set_keeps_its_language():
    values = {"title": "T", "level": "basic", "requirements": [], "final": [], "language": "ru"}

    assert build_preparation(uuid.uuid4(), "ann", "text", values).language == "ru"
    # Runs started before languages existed are English.
    del values["language"]
    assert build_preparation(uuid.uuid4(), "ann", "text", values).language == "en"
