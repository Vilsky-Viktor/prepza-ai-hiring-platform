import uuid
from types import SimpleNamespace

from testee_common.http import http
from testee_common.http.http import bearer

from library.repositories import preparations, quality
from library.services import outbox
from tests.unit.api.v1.test_internal import token

QUESTION_ID = uuid.uuid4()
OPTIONS = [{"answer": "Debit cash", "correct": False}, {"answer": "Credit cash", "correct": True}]


class NoCalls:
    """Records any request to another service."""

    def __init__(self):
        self.calls = []

    async def request(self, method, url, **kwargs):
        self.calls.append((method, url))

    async def post(self, url, **kwargs):
        self.calls.append(("POST", url))


def test_a_replaced_question_leaves_past_answers_alone(client, monkeypatch):
    """The fix applies to candidates who start after it: no service is asked to mark past
    answers again."""
    replaced = []
    outgoing = NoCalls()

    async def fake_replace(session, question_id, text, options):
        replaced.append((question_id, text, options))

    async def nothing(session, *args, **kwargs):
        return None

    async def fake_flush():
        return None

    async def fake_set(session, question_id):
        return SimpleNamespace(id=uuid.uuid4())

    monkeypatch.setattr(preparations, "set_content", fake_replace)
    monkeypatch.setattr(preparations, "question", nothing)
    monkeypatch.setattr(quality, "current_flag", nothing)
    monkeypatch.setattr(quality, "archive", nothing)
    monkeypatch.setattr(preparations, "get_for_question", fake_set)
    monkeypatch.setattr(outbox, "flush_quietly", fake_flush)
    monkeypatch.setattr(http, "get_client", lambda: outgoing)

    response = client.put(
        f"/internal/questions/{QUESTION_ID}",
        json={"text": "What is debit?", "options": OPTIONS},
        headers=bearer(token()),
    )

    assert response.status_code == 204
    assert replaced == [(QUESTION_ID, "What is debit?", OPTIONS)]
    assert outgoing.calls == []
