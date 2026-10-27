import uuid

from prepza_common.http.http import bearer

from app.storage import reuse
from tests.unit.test_internal import token

SOURCE_ID = uuid.uuid4()
OPTIONS = [{"answer": "Debit cash", "correct": True}, {"answer": "Credit cash", "correct": False}]


def find(client, body):
    return client.post("/internal/reuse", json=body, headers=bearer(token()))


def test_proven_questions_are_offered_for_a_similar_topic(client, monkeypatch):
    asked = {}

    async def fake_find(embedding, level, language, count):
        asked.update(embedding=embedding, level=level, language=language, count=count)

        return [(SOURCE_ID, "A customer pays cash. Which entry is recorded?", OPTIONS)]

    monkeypatch.setattr(reuse, "find", fake_find)

    response = find(
        client, {"embedding": [0.1, 0.2], "level": "basic", "language": "ru", "count": 5}
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "source_id": str(SOURCE_ID),
            "text": "A customer pays cash. Which entry is recorded?",
            "options": OPTIONS,
        }
    ]
    assert asked == {"embedding": [0.1, 0.2], "level": "basic", "language": "ru", "count": 5}


def test_count_is_bounded(client):
    assert find(client, {"embedding": [0.1], "level": "basic", "count": 0}).status_code == 422
    assert find(client, {"embedding": [0.1], "level": "basic", "count": 101}).status_code == 422


def test_vectors_are_written_the_way_pgvector_reads_them():
    assert reuse.as_vector([0.5, -1.0, 2e-05]) == "[0.5,-1.0,2e-05]"
