"""Batch work's storage in memory and OpenAI's Batch API as a script, for the batch work tests."""

import asyncio
import itertools
import uuid
from types import SimpleNamespace

from app.integrations import openai_batch
from app.storage import batch_work as storage


class FakeStore:
    """The batch_work table as a dict by id."""

    def __init__(self):
        self.rows: dict = {}

    def install(self, monkeypatch):
        for name in (
            "add",
            "unsent",
            "sent_batches",
            "in_batch",
            "set_batch",
            "next_step",
            "remove",
        ):
            monkeypatch.setattr(storage, name, getattr(self, name))

    async def add(self, kind, subject_id, key, step, payload, body):
        if any(
            (r.kind, r.subject_id, r.key) == (kind, subject_id, key) for r in self.rows.values()
        ):
            return

        row = SimpleNamespace(
            id=uuid.uuid4(),
            kind=kind,
            subject_id=subject_id,
            key=key,
            step=step,
            attempt=0,
            payload=payload,
            body=body,
            batch_id=None,
        )
        self.rows[row.id] = row

    async def unsent(self, limit):
        return [row for row in self.rows.values() if row.batch_id is None][:limit]

    async def sent_batches(self):
        return sorted({row.batch_id for row in self.rows.values() if row.batch_id})

    async def in_batch(self, batch_id):
        return [row for row in self.rows.values() if row.batch_id == batch_id]

    async def set_batch(self, ids, batch_id):
        for work_id in ids:
            self.rows[work_id].batch_id = batch_id

    async def next_step(self, work_id, batch_id, step, attempt, payload, body):
        row = self.rows.get(work_id)

        if row is not None and row.batch_id == batch_id:
            row.step, row.attempt, row.payload, row.body = step, attempt, payload, body
            row.batch_id = None

    async def remove(self, ids):
        for work_id in ids:
            self.rows.pop(work_id, None)


class FakeBatches:
    """OpenAI's Batch API: what was sent, and each batch answered by `answer(body)` (a reply's
    text, or None for a request that failed)."""

    def __init__(self, answer):
        self.answer = answer
        self.sent: dict[str, dict] = {}
        self.ids = (f"batch-{n}" for n in itertools.count(1))

    def install(self, monkeypatch):
        monkeypatch.setattr(openai_batch, "submit", self.submit)
        monkeypatch.setattr(openai_batch, "status", self.status)
        monkeypatch.setattr(openai_batch, "results", self.results)

    async def submit(self, requests):
        batch_id = next(self.ids)
        self.sent[batch_id] = requests

        return batch_id

    async def status(self, batch_id):
        return "completed", batch_id

    async def results(self, file_id):
        replies = {key: self.answer(body) for key, body in self.sent[file_id].items()}
        used = [(key, "gpt-6.1-sol", {"input_tokens": 100, "output_tokens": 10}) for key in replies]

        return replies, used


def run_batches(monkeypatch, answer, rounds: int = 1) -> FakeBatches:
    """Sends the waiting batch work and moves on what comes back, `rounds` times."""
    from app.services import batch_work

    batches = FakeBatches(answer)
    batches.install(monkeypatch)

    async def run():
        for _ in range(rounds):
            await batch_work.submit_pending()
            await batch_work.collect_finished()

    asyncio.run(run())

    return batches
