"""A long conversation opens on its latest messages; earlier ones come a page at a time, and
`earlier` says whether more are left."""

import httpx
from prepza_common.http.http import bearer

from assistant.constants.chat import Source
from assistant.main import app
from assistant.repositories import conversations, messages
from assistant.services import conversation_pages


def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://assistant")


def test_a_conversation_opens_on_its_latest_messages_and_pages_back(run, user, monkeypatch):
    uid, token = user
    monkeypatch.setattr(conversation_pages, "MESSAGES_SHOWN", 2)

    async def scenario():
        chat = await conversations.create(uid, None, "Long chat")

        for number in range(5):
            await messages.add_question(chat.id, f"Question {number}?", Source.TEXT)

        async with client() as api:
            opened = (await api.get(f"/conversations/{chat.id}", headers=bearer(token))).json()
            pages = [opened]

            while pages[-1]["earlier"]:
                first = pages[-1]["messages"][0]["id"]
                path = f"/conversations/{chat.id}/messages?before={first}"
                pages.append((await api.get(path, headers=bearer(token))).json())

        return [[item["content"] for item in page["messages"]] for page in pages], [
            page["earlier"] for page in pages
        ]

    shown, earlier = run(scenario())

    # Oldest first in each page, the latest page first.
    assert shown == [
        ["Question 3?", "Question 4?"],
        ["Question 1?", "Question 2?"],
        ["Question 0?"],
    ]
    assert earlier == [True, True, False]


def test_another_users_conversation_has_no_pages(run, user):
    _uid, token = user

    async def scenario():
        chat = await conversations.create("someone-else", None, "Theirs")
        question = await messages.add_question(chat.id, "Mine?", Source.TEXT)

        async with client() as api:
            path = f"/conversations/{chat.id}/messages?before={question.id}"

            return (await api.get(path, headers=bearer(token))).status_code

    assert run(scenario()) == 404
