"""The routes taking a generation's, a template's or a quality pattern's id are the
superadmin's: everyone else is refused (access_matrix, .claude/rules/testing.md, Security)."""

from uuid import uuid4

import access_matrix
import pytest
from access_matrix import Side, World, user_id
from sqlalchemy import select

from generation.constants.kinds import GenerationKind
from generation.core.db import Session
from generation.integrations.redis import get_redis
from generation.main import app
from generation.models.patterns import QualityPattern
from generation.repositories import generations, patterns
from tests.integration.transactions import transaction

OWNED = {"generation_id", "pattern_id"}

NOT_OWNED = {}

# Templates and their questions are library's, asked for each request.
VALUES = {"template_id": str(uuid4()), "question_id": str(uuid4())}

BODIES = {"POST /superadmin/generations/{generation_id}/review": {"selected": [0]}}


async def side(kind: str) -> Side:
    """A template's generation and a proposed quality pattern."""
    generation = await transaction(
        generations.create, "sam", "Matrix", kind=GenerationKind.TEMPLATE
    )
    text = f"Matrix {kind} {uuid4()}"
    await transaction(patterns.add, text, "rewrite", 1)

    async with Session() as session:
        pattern = await session.scalar(select(QualityPattern.id).where(QualityPattern.text == text))

    return Side(user_id(kind), {"generation_id": str(generation.id), "pattern_id": str(pattern)})


@pytest.fixture
def world(run, monkeypatch):
    """The routes' Redis client is dropped after, as it belongs to the test's event loop."""

    async def make():
        return World(await side("mine"), await side("theirs"))

    yield access_matrix.enter(monkeypatch, run(make()))

    get_redis.cache_clear()


def test_every_route_taking_an_id_is_in_the_matrix_or_listed_with_why():
    assert access_matrix.unlisted(app, OWNED, NOT_OWNED) == []


@pytest.mark.parametrize("route", access_matrix.routes(app, OWNED, NOT_OWNED), ids=str)
def test_only_whoever_may_gets_through(route, world, run):
    found, statuses = run(access_matrix.outcomes(app, route, world, BODIES, VALUES))

    assert found == access_matrix.expected(route, world, {}), str(statuses)
