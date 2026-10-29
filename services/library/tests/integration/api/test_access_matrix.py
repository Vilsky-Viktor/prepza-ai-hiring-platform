"""The question bank's routes taking an id: the superadmin's refuse everyone else, and a
template's public pages never show a company's own test by its id (access_matrix); the /internal
routes taking a set with one of its topics or questions refuse another set's, and a call without
this service's token (internal_matrix; .claude/rules/testing.md, Security)."""

from uuid import uuid4

import access_matrix
import internal_matrix
import pytest
from access_matrix import REFUSED, Side, World, user_id
from sqlalchemy import select

from library.config import settings
from library.core.db import Session
from library.core.security import SERVICE_NAME
from library.main import app
from library.models.quality import QuestionRevision
from library.repositories import preparations, quality
from tests.integration import factories
from tests.integration.transactions import transaction

# The template's ids, and `key`: a company's own test, which is no template.
OWNED = {"key"}

NOT_OWNED = {}

# A set with one of its topics or questions: companies asks about its interview's set.
INTERNAL_OWNED = {"set_id", "topic_id", "question_id"}
OWN = "The user's own, as rounds vouches for its candidate."
NOT_SCOPED = {
    "GET /internal/questions/{question_id}/rating": OWN,
    "GET /internal/questions/{question_id}/reports/mine": OWN,
}
KEY = (settings.service_secret, SERVICE_NAME)

VALUES = {}

BODIES = {"PATCH /superadmin/templates/{template_id}/title": {"title": "Matrix"}}

# Nobody, its own company included, reads a company's test as a template: companies reads its
# tests through its own checked routes.
NO_ONE = {"owner": REFUSED, "signed out": REFUSED}
EXCEPTIONS = {"GET /templates/{key}": NO_ONE, "GET /templates/{key}/sample": NO_ONE}


async def side(kind: str) -> Side:
    """A company's test, and a template with a question replaced once (its revision)."""
    company = str(uuid4())
    key = await factories.interview(owner=company)
    template = await factories.interview(title=f"Matrix {kind}", template=True)
    content = await transaction(preparations.get_content, template)
    topic = content.topics[0]
    question = topic.questions[0].id
    await transaction(quality.archive, question)

    async with Session() as session:
        revision = await session.scalar(
            select(QuestionRevision.id).where(QuestionRevision.question_id == question)
        )

    ids = {
        "key": key,
        "template_id": template,
        "set_id": template,
        "topic_id": topic.id,
        "question_id": question,
        "revision_id": revision,
    }

    return Side(user_id(kind), {name: str(value) for name, value in ids.items()})


@pytest.fixture
def world(run, monkeypatch):
    async def make():
        return World(await side("mine"), await side("theirs"))

    return access_matrix.enter(monkeypatch, run(make()))


def test_every_route_taking_an_id_is_in_the_matrix_or_listed_with_why():
    assert access_matrix.unlisted(app, OWNED, NOT_OWNED) == []


@pytest.mark.parametrize("route", access_matrix.routes(app, OWNED, NOT_OWNED), ids=str)
def test_only_whoever_may_gets_through(route, world, run):
    found, statuses = run(access_matrix.outcomes(app, route, world, BODIES, VALUES))

    assert found == access_matrix.expected(route, world, EXCEPTIONS), str(statuses)


def test_every_internal_route_taking_two_ids_is_scoped_or_listed_with_why():
    assert internal_matrix.unlisted(app, INTERNAL_OWNED, NOT_SCOPED, {}) == []


@pytest.mark.parametrize(
    "route", internal_matrix.routes(app, INTERNAL_OWNED, NOT_SCOPED, {}), ids=str
)
def test_only_the_scoped_object_gets_through(route, world, run):
    found, statuses = run(internal_matrix.outcomes(app, route, world, KEY, BODIES, VALUES))

    assert found == internal_matrix.expected(route, {}), str(statuses)
