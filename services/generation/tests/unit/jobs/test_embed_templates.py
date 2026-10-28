import asyncio

from generation.integrations import library, llm
from generation.jobs.embed_templates import embed_templates


class FakeEmbeddings:
    async def aembed_documents(self, texts):
        return [[float(len(text))] for text in texts]


def test_embeds_template_topics_until_none_are_missing(monkeypatch):
    batches = [
        [{"id": "t1", "title": "Ledgers", "subtopics": ["Accruals"]}],
        [{"id": "t2", "title": "Payroll", "subtopics": []}],
        [],
    ]
    saved = {}

    async def missing(limit):
        return batches.pop(0)

    async def save(embeddings):
        saved.update(embeddings)

    monkeypatch.setattr(library, "missing_embeddings", missing)
    monkeypatch.setattr(library, "save_embeddings", save)
    monkeypatch.setattr(llm, "get_embeddings", FakeEmbeddings)

    assert asyncio.run(embed_templates()) == 2
    assert set(saved) == {"t1", "t2"}
