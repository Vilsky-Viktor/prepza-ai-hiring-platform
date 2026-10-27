import uuid
from types import SimpleNamespace

from prepza_common.http.http import bearer

from app.storage import preparations
from tests.unit.test_internal import token

TEMPLATE_ID = uuid.uuid4()


def question(pool, text):
    return SimpleNamespace(
        id=uuid.uuid4(),
        text=text,
        pool=pool,
        options=[{"answer": "a", "correct": True}, {"answer": "b", "correct": False}],
    )


def test_practice_gets_only_practice_questions_and_skips_empty_topics(client, monkeypatch):
    template = SimpleNamespace(
        id=TEMPLATE_ID,
        kind="template",
        title="Backend",
        level="hard",
        topics=[
            SimpleNamespace(
                id=uuid.uuid4(),
                title="Python",
                questions=[question("practice", "Open?"), question("company", "Secret?")],
            ),
            SimpleNamespace(id=uuid.uuid4(), title="SQL", questions=[question("company", "S?")]),
        ],
    )

    async def get_content(set_id):
        return template if set_id == TEMPLATE_ID else None

    monkeypatch.setattr(preparations, "get_content", get_content)
    headers = bearer(token())

    found = client.get(f"/internal/templates/{TEMPLATE_ID}/practice", headers=headers).json()
    missing = client.get(f"/internal/templates/{uuid.uuid4()}/practice", headers=headers)

    # Rounds gives each question the seconds of the template's level.
    assert found["level"] == "hard"
    assert [topic["title"] for topic in found["topics"]] == ["Python"]
    assert [q["text"] for q in found["topics"][0]["questions"]] == ["Open?"]
    assert missing.status_code == 404
