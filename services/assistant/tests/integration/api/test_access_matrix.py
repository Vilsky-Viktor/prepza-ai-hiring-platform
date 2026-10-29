"""Every route taking the id of a user's conversation, answer, pending action or connected app
lets that user through and refuses another user and anyone signed out (access_matrix,
.claude/rules/testing.md, Security)."""

from uuid import uuid4

import access_matrix
import pytest
from access_matrix import Side, World, user_id

from assistant.main import app
from assistant.repositories import actions
from tests.integration.api.v1.test_votes import answered
from tests.integration.repositories.test_oauth import connect

OWNED = {"conversation_id", "message_id", "action_id", "connection_id"}

# A company's id only picks the user's own conversations, or a greeting companies checks with
# the user's own token.
COMPANY_FILTER = "Only filters the caller's own; companies checks the company with their token."
APPROVAL = "An app's connection request is the caller's to approve: its id comes from the app."
NOT_OWNED = {
    "GET /welcome": COMPANY_FILTER,
    "GET /conversations": COMPANY_FILTER,
    "GET /connect/{request_id}": APPROVAL,
    "POST /connect/{request_id}/approve": APPROVAL,
    "POST /connect/{request_id}/deny": APPROVAL,
    "PUT /help/answers/{answer_id}/vote": "The help chat's answers: visitors vote, once per address.",
}

BODIES = {"PUT /conversations/{conversation_id}/messages/{message_id}/vote": {"value": 1}}


async def side(kind: str) -> Side:
    """A user's conversation with an answer, an action waiting in it and a connected app."""
    user = user_id(kind)
    conversation, _, answer = await answered(user)
    action = uuid4()
    await actions.save(
        action,
        {"user_id": user, "conversation_id": str(conversation), "company_id": None, "tool": "t"},
    )
    grant, _ = await connect(user)
    ids = {
        "conversation_id": conversation,
        "message_id": answer,
        "action_id": action,
        "connection_id": grant.id,
    }

    return Side(user, {name: str(value) for name, value in ids.items()})


@pytest.fixture
def world(run, monkeypatch):
    async def make():
        return World(await side("mine"), await side("theirs"))

    return access_matrix.enter(monkeypatch, run(make()))


def test_every_route_taking_an_id_is_in_the_matrix_or_listed_with_why():
    assert access_matrix.unlisted(app, OWNED, NOT_OWNED) == []


@pytest.mark.parametrize("route", access_matrix.routes(app, OWNED, NOT_OWNED), ids=str)
def test_only_whoever_may_gets_through(route, world, run):
    found, statuses = run(access_matrix.outcomes(app, route, world, BODIES, {}))

    assert found == access_matrix.expected(route, world, {}), str(statuses)
