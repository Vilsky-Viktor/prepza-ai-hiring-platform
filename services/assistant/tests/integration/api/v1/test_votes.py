"""Votes on the assistant's answers through the routes, against the real database and a
throwaway Auth emulator user: one vote an answer, changed or cleared, shown when the
conversation is opened, and only on the user's own answers."""

from prepza_common.http.http import bearer

from assistant.constants.chat import Status
from assistant.models.answers import Answer
from assistant.repositories import conversations, messages
from assistant.services import conversations as conversation_service
from tests.integration.api.v1.test_chat import client
from tests.integration.transactions import transaction

TRACE = "a" * 32


async def answered(user_id):
    """A conversation of `user_id`'s with a question and an answer written in trace TRACE."""
    conversation = await transaction(conversations.create, user_id, None, "Votes")
    question = await transaction(messages.add_question, conversation.id, "Who passed?", "text")
    answer_id = await transaction(
        messages.add_answer,
        conversation.id,
        Answer(parts=["Ann passed."], trace_id=TRACE),
        Status.COMPLETE,
    )

    return conversation.id, question.id, answer_id


def test_the_owner_votes_changes_and_clears_and_sees_it_when_opening(run, user, monkeypatch):
    uid, token = user
    headers = bearer(token)
    mirrored = []

    async def mirror_vote(trace_id, current):
        mirrored.append(trace_id)

    monkeypatch.setattr(conversation_service, "mirror_vote", mirror_vote)

    async def scenario():
        conversation_id, _, answer_id = await answered(uid)
        path = f"/conversations/{conversation_id}/messages/{answer_id}/vote"
        seen = []

        async with client() as api:
            for value in (1, -1):
                await api.put(path, json={"value": value}, headers=headers)
                seen.append(await transaction(messages.vote_of, answer_id))

            opened = (await api.get(f"/conversations/{conversation_id}", headers=headers)).json()
            cleared = await api.put(path, json={"value": None}, headers=headers)

        return seen, opened, cleared, await transaction(messages.vote_of, answer_id)

    seen, opened, cleared, after = run(scenario())

    assert seen == [1, -1]
    assert [message["vote"] for message in opened["messages"]] == [None, -1]
    assert (cleared.status_code, after) == (204, None)
    assert mirrored == [TRACE, TRACE, TRACE]


def test_no_vote_on_someone_elses_answer_or_on_a_question(run, user, monkeypatch):
    _, token = user
    headers = bearer(token)

    async def mirror_vote(trace_id, current):
        return None

    monkeypatch.setattr(conversation_service, "mirror_vote", mirror_vote)

    async def scenario():
        theirs, _, their_answer = await answered("someone-else")
        mine, my_question, _ = await answered(user[0])

        async with client() as api:
            other = await api.put(
                f"/conversations/{theirs}/messages/{their_answer}/vote",
                json={"value": 1},
                headers=headers,
            )
            # Their answer named under the user's own conversation.
            mixed = await api.put(
                f"/conversations/{mine}/messages/{their_answer}/vote",
                json={"value": 1},
                headers=headers,
            )
            question = await api.put(
                f"/conversations/{mine}/messages/{my_question}/vote",
                json={"value": 1},
                headers=headers,
            )

        return other, mixed, question, await transaction(messages.vote_of, their_answer)

    other, mixed, question, kept = run(scenario())

    for refused in (other, mixed, question):
        assert refused.status_code == 404
        assert refused.json()["detail"] == "Not found"

    assert kept is None
