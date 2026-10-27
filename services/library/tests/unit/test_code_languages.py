import uuid

from prepza_common.http.http import bearer

from app.storage import code
from tests.unit.test_internal import token

QUESTION = uuid.uuid4()


def test_generation_reads_untagged_examples_and_saves_their_languages(client, monkeypatch):
    saved = []

    asked = []

    async def untagged(limit, fence, after):
        asked.append((limit, fence, after))

        return [(QUESTION, "Q?\n```\nx\n```")]

    async def tag(languages, fence):
        saved.append((languages, fence))

    monkeypatch.setattr(code, "untagged", untagged)
    monkeypatch.setattr(code, "tag", tag)

    listed = client.get("/internal/code/untagged?limit=5", headers=bearer(token()))
    put = client.put(
        "/internal/code/languages",
        json=[{"id": str(QUESTION), "language": "c++"}],
        headers=bearer(token()),
    )
    # The ones tagged "text", checked again, page by page.
    client.get(f"/internal/code/untagged?text=true&after={QUESTION}", headers=bearer(token()))
    client.put(
        "/internal/code/languages?text=true",
        json=[{"id": str(QUESTION), "language": "javascript"}],
        headers=bearer(token()),
    )

    assert listed.json() == [{"id": str(QUESTION), "text": "Q?\n```\nx\n```"}]
    assert put.status_code == 204
    assert asked == [(5, "```\n", None), (100, "```text\n", QUESTION)]
    assert saved == [({QUESTION: "c++"}, "```\n"), ({QUESTION: "javascript"}, "```text\n")]


def test_a_language_that_could_break_the_fence_is_refused(client, monkeypatch):
    saved = []

    async def tag(languages, fence):
        saved.append(languages)

    monkeypatch.setattr(code, "tag", tag)

    response = client.put(
        "/internal/code/languages",
        json=[{"id": str(QUESTION), "language": "python\n```"}],
        headers=bearer(token()),
    )

    assert response.status_code == 422
    assert saved == []


def test_only_services_reach_the_examples(client):
    assert client.get("/internal/code/untagged").status_code == 401
