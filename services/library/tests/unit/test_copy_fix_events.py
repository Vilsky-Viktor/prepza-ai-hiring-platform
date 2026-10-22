"""question.fixed, library's own event: a fixed bank question's copies are fixed a batch at a
time, and a push that runs out of time answers 503 so Pub/Sub brings it back."""

import uuid

from app.services import copy_fixes
from app.storage import copy_fixes as copy_storage
from tests.unit.test_answer_events import push

QUESTION_ID = uuid.uuid4()
EVENT = {"question_id": str(QUESTION_ID), "text": "Old?", "options": [{"answer": "A"}]}


def test_a_fixed_questions_copies_are_fixed_until_none_are_left(client, monkeypatch):
    batches = [copy_fixes.COPY_FIX_BATCH, copy_fixes.COPY_FIX_BATCH, 3]
    asked = []

    async def fix_copies(question_id, old_text, old_options):
        asked.append((question_id, old_text, old_options))

        return batches.pop(0)

    monkeypatch.setattr(copy_storage, "fix_copies", fix_copies)

    response = client.post("/internal/events", json=push("question.fixed", EVENT))

    assert response.status_code == 204
    assert asked == [(QUESTION_ID, "Old?", [{"answer": "A"}])] * 3


def test_a_push_out_of_time_with_copies_left_comes_back(client, monkeypatch):
    async def fix_copies(question_id, old_text, old_options):
        return copy_fixes.COPY_FIX_BATCH

    monkeypatch.setattr(copy_storage, "fix_copies", fix_copies)
    monkeypatch.setattr(copy_fixes, "COPY_FIX_SECONDS", -1)

    response = client.post("/internal/events", json=push("question.fixed", EVENT))

    assert response.status_code == 503
    assert response.headers["Retry-After"] == "10"
