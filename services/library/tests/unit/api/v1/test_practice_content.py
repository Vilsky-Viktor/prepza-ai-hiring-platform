import uuid
from types import SimpleNamespace

from prepza_common.http.http import bearer

from library.repositories import practice_matches, preparations
from tests.unit.api.v1.test_internal import token

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

    async def get_content(session, set_id):
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


def test_companies_gets_an_interviews_matching_practice_topics(client, monkeypatch):
    topic_id = uuid.uuid4()

    async def practice_topics(session, set_id):
        return [topic_id] if set_id == TEMPLATE_ID else []

    monkeypatch.setattr(practice_matches, "practice_topics", practice_topics)

    found = client.get(f"/internal/sets/{TEMPLATE_ID}/practice-topics", headers=bearer(token()))

    assert found.json() == {"topic_ids": [str(topic_id)]}
