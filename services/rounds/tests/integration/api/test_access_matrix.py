"""Every route taking the id of a candidate's session or a talent's practice round lets its own
user through and refuses another user and anyone signed out (access_matrix,
.claude/rules/testing.md, Security)."""

from uuid import uuid4

import access_matrix
import internal_matrix
import pytest
from access_matrix import Side, World, user_id

from rounds.main import app
from tests.integration import factories

OWNED = {"session_id", "question_id", "round_id"}

# A template is the question bank's, open to every talent: each one's rounds on it are read by
# the caller's own id.
TEMPLATE = "A public template: the talent's own rounds on it are read by their id."
NOT_OWNED = {
    "POST /practice/{template_id}": TEMPLATE,
    "GET /practice/{template_id}/size": "Public on purpose (test_route_guards): a template's size.",
    "GET /practice/{template_id}/rounds": TEMPLATE,
    "GET /practice/{template_id}/progress": TEMPLATE,
}

BODIES = {
    "POST /sessions/{session_id}/answers": lambda ids: {
        "question_id": ids["question_id"],
        "option_index": 0,
    },
    "POST /sessions/{session_id}/questions/{question_id}/reports": {"reason": "wrong_answer"},
}

# Path values that aren't ids: voice mode's phrase.
VALUES = {"phrase": "end"}


async def side(kind: str) -> Side:
    """A user with an interview session running and a practice round."""
    user = user_id(kind)
    topic = factories.topic()
    sections = await factories.created(user, uuid4(), [topic], 60, company_id=uuid4())
    practice = uuid4()
    await factories.created(user, practice, [factories.topic()], None, practice=True)
    ids = {
        "session_id": sections[0].id,
        "question_id": topic.questions[0].id,
        "round_id": practice,
    }

    return Side(user, {name: str(value) for name, value in ids.items()})


@pytest.fixture
def world(run, monkeypatch):
    async def make():
        return World(await side("mine"), await side("theirs"))

    return access_matrix.enter(monkeypatch, run(make()))


def test_every_route_taking_an_id_is_in_the_matrix_or_listed_with_why():
    assert access_matrix.unlisted(app, OWNED, NOT_OWNED) == []


def test_no_internal_route_takes_an_id_with_another_that_scopes_it():
    """None today: one that comes is scoped in the internal matrix (internal_matrix)."""
    assert internal_matrix.unlisted(app, OWNED, {}, {}) == []


@pytest.mark.parametrize("route", access_matrix.routes(app, OWNED, NOT_OWNED), ids=str)
def test_only_whoever_may_gets_through(route, world, run):
    found, statuses = run(access_matrix.outcomes(app, route, world, BODIES, VALUES))

    assert found == access_matrix.expected(route, world, {}), str(statuses)
