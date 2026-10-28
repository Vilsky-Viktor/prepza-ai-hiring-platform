"""question.fixed, library's own event: a fixed bank question's copies are fixed a batch at a
time, each company told, and a push that runs out of time answers 503 so Pub/Sub brings it
back."""

import uuid

from event_pushes import push
import pytest

from library.repositories import copy_fixes as copy_storage
from library.services import copy_fixes

QUESTION_ID = uuid.uuid4()
EVENT = {"question_id": str(QUESTION_ID), "text": "Old?", "options": [{"answer": "A"}]}


@pytest.fixture
def told(monkeypatch):
    """The copies whose companies are told; no database."""
    copies = []

    async def tell_owner(session, question_id, kind):
        copies.append(question_id)

    monkeypatch.setattr(copy_fixes, "tell_owner", tell_owner)

    return copies


def batch(size):
    return [uuid.uuid4() for _ in range(size)]


def test_a_fixed_questions_copies_are_fixed_until_none_are_left(client, monkeypatch, told):
    batches = [batch(copy_fixes.COPY_FIX_BATCH), batch(copy_fixes.COPY_FIX_BATCH), batch(3)]
    fixed = [copy for found in batches for copy in found]
    asked = []

    async def fix_copies(session, question_id, old_text, old_options):
        asked.append((question_id, old_text, old_options))

        return batches.pop(0)

    monkeypatch.setattr(copy_storage, "fix_copies", fix_copies)

    response = client.post("/internal/events", json=push("question.fixed", EVENT))

    assert response.status_code == 204
    assert asked == [(QUESTION_ID, "Old?", [{"answer": "A"}])] * 3
    assert told == fixed


def test_a_push_out_of_time_with_copies_left_comes_back(client, monkeypatch, told):
    async def fix_copies(session, question_id, old_text, old_options):
        return batch(copy_fixes.COPY_FIX_BATCH)

    monkeypatch.setattr(copy_storage, "fix_copies", fix_copies)
    monkeypatch.setattr(copy_fixes, "COPY_FIX_SECONDS", -1)

    response = client.post("/internal/events", json=push("question.fixed", EVENT))

    assert response.status_code == 503
    assert response.headers["Retry-After"] == "10"
