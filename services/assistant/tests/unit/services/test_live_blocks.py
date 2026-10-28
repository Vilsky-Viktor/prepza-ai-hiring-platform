import asyncio

import httpx

from assistant.integrations import services
from assistant.services.live_blocks import live

CANDIDATES = [
    {"id": "c1", "email": "ann@example.com", "status": "finished", "grade": 82, "passed": True},
    {"id": "c3", "email": "cy@example.com", "status": "invited", "grade": None, "passed": None},
]


def companies(monkeypatch, answers: dict):
    """Companies answering each path (404 for any other); the tokens it was called with."""
    tokens = []

    async def get(service, path, query, token, language, via=None):
        tokens.append(token)
        status, body = answers.get(path, (404, {"detail": "Not found"}))

        return httpx.Response(status, json=body, request=httpx.Request("GET", "http://x"))

    monkeypatch.setattr(services, "get", get)

    return tokens


def test_opening_fetches_the_blocks_again_with_the_viewers_token_and_drops_whats_gone(
    monkeypatch,
):
    tokens = companies(
        monkeypatch,
        {
            "/interviews/i1/candidates": (200, CANDIDATES),
            "/interviews/i2": (200, {"id": "i2", "title": "Backend", "status": "new"}),
        },
    )
    stored = [
        {
            "kind": "candidate_rows",
            # c2 was erased since.
            "refs": [{"id": "c1", "interview_id": "i1"}, {"id": "c2", "interview_id": "i1"}],
            "links": ["/l/c1", "/l/c2"],
        },
        # An interview the viewer can't see any more.
        {"kind": "interview", "refs": [{"id": "gone"}], "links": ["/l/gone"]},
        {"kind": "interview", "refs": [{"id": "i2"}], "links": ["/l/i2"]},
        {"kind": "link", "refs": [], "links": ["/settings"]},
    ]

    shown = asyncio.run(live(stored, "viewer-token", "en"))

    assert [block["kind"] for block in shown] == ["candidate_rows", "interview", "link"]
    assert [item["id"] for item in shown[0]["items"]] == ["c1"]
    assert shown[0]["items"][0]["email"] == "ann@example.com"
    assert shown[0]["links"] == ["/l/c1"]
    assert shown[1]["items"][0]["title"] == "Backend"
    assert set(tokens) == {"viewer-token"}


def test_companies_not_answering_shows_nothing_stale(monkeypatch):
    companies(monkeypatch, {"/interviews/i1/candidates": (503, {})})
    stored = [
        {"kind": "candidate_rows", "refs": [{"id": "c1", "interview_id": "i1"}], "links": ["/l"]}
    ]

    assert asyncio.run(live(stored, "t", "en")) == []
