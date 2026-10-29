"""The routes taking a generation's, a template's or a quality pattern's id are the
superadmin's: everyone else is refused (access_matrix); the /internal routes taking a company's
generation, or a question with its set, refuse another company's or set's, and a call without
this service's token (internal_matrix; .claude/rules/testing.md, Security)."""

from uuid import uuid4

import access_matrix
import internal_matrix
import pytest
from access_matrix import Side, World, user_id
from sqlalchemy import select

from generation.api.v1 import internal, superadmin
from generation.config import settings
from generation.constants.kinds import GenerationKind
from generation.core.db import Session
from generation.core.security import SERVICE_NAME
from generation.integrations import library
from generation.integrations.redis import get_redis
from generation.main import app
from generation.models.patterns import QualityPattern
from generation.repositories import generations, patterns
from generation.schemas.regenerate import QuestionContext
from tests.integration.transactions import transaction

OWNED = {"generation_id", "pattern_id"}

NOT_OWNED = {}

# A company's generation with its company; a question with its set (in the body), as companies
# asks for its interview's.
INTERNAL_OWNED = {"generation_id", "company_id", "question_id", "set_id"}
BODY_IDS = {"POST /internal/questions/{question_id}/regenerate": ("set_id",)}
KEY = (settings.service_secret, SERVICE_NAME)

# Templates and their questions are library's, asked for each request.
VALUES = {"template_id": str(uuid4()), "question_id": str(uuid4())}

BODIES = {
    "POST /superadmin/generations/{generation_id}/review": {"selected": [0]},
    "POST /internal/generations/{generation_id}/review": {"selected": [0]},
    "POST /internal/questions/{question_id}/regenerate": lambda ids: {
        "user_id": "ann",
        "set_id": ids["set_id"],
    },
}


async def side(kind: str) -> Side:
    """A template's generation, a company's, a proposed quality pattern and a question of a
    company's set."""
    generation = await transaction(
        generations.create, "sam", "Matrix", kind=GenerationKind.TEMPLATE
    )
    company = uuid4()
    company_generation = await transaction(generations.create, "ann", "Matrix", company)
    text = f"Matrix {kind} {uuid4()}"
    await transaction(patterns.add, text, "rewrite", 1)

    async with Session() as session:
        pattern = await session.scalar(select(QualityPattern.id).where(QualityPattern.text == text))

    ids = {
        "generation_id": generation.id,
        "pattern_id": pattern,
        "company_id": company,
        "company_generation_id": company_generation.id,
        "set_question_id": uuid4(),
        "set_id": uuid4(),
    }

    return Side(user_id(kind), {name: str(value) for name, value in ids.items()})


def companies(world: World) -> World:
    """The world with each side's company generation and set question as those its routes
    name."""
    for side in (world.mine, world.theirs):
        named = {"generation_id": "company_generation_id", "question_id": "set_question_id"}
        side.ids = side.ids | {name: side.ids[key] for name, key in named.items()}

    return world


@pytest.fixture
def world(run, monkeypatch):
    """The routes' Redis client is dropped after, as it belongs to the test's event loop."""

    async def make():
        return World(await side("mine"), await side("theirs"))

    made = run(make())
    sets = {side.ids["set_question_id"]: side.ids["set_id"] for side in (made.mine, made.theirs)}

    async def question_context(question_id):
        """Library knows each side's question in its own company's set; any other is the
        superadmin's template's (VALUES)."""
        set_id = sets.get(str(question_id))

        return QuestionContext(
            set_id=set_id or VALUES["template_id"],
            kind="interview" if set_id else "template",
            owner_id=str(uuid4()),
            level="medium",
            topic="Python",
            subtopics=[],
            existing=[],
        )

    async def no_model(question_id, context):
        """No model is asked: the route answers it couldn't make a question (502)."""
        return

    monkeypatch.setattr(library, "get_question_context", question_context)
    monkeypatch.setattr(internal, "regenerate", no_model)
    monkeypatch.setattr(superadmin, "regenerate", no_model)

    yield access_matrix.enter(monkeypatch, made)

    get_redis.cache_clear()


def test_every_route_taking_an_id_is_in_the_matrix_or_listed_with_why():
    assert access_matrix.unlisted(app, OWNED, NOT_OWNED) == []


@pytest.mark.parametrize("route", access_matrix.routes(app, OWNED, NOT_OWNED), ids=str)
def test_only_whoever_may_gets_through(route, world, run):
    found, statuses = run(access_matrix.outcomes(app, route, world, BODIES, VALUES))

    assert found == access_matrix.expected(route, world, {}), str(statuses)


def test_every_internal_route_taking_two_ids_is_scoped_or_listed_with_why():
    assert internal_matrix.unlisted(app, INTERNAL_OWNED, {}, BODY_IDS) == []


@pytest.mark.parametrize(
    "route", internal_matrix.routes(app, INTERNAL_OWNED, {}, BODY_IDS), ids=str
)
def test_only_the_scoped_object_gets_through(route, world, run):
    found, statuses = run(
        internal_matrix.outcomes(app, route, companies(world), KEY, BODIES, VALUES)
    )

    assert found == internal_matrix.expected(route, {}), str(statuses)
