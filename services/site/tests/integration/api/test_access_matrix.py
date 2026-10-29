"""The routes taking a news post's id are the superadmin's: everyone else is refused; the
public pages' keys name content open to all (access_matrix, .claude/rules/testing.md,
Security)."""

from datetime import date

import access_matrix
import internal_matrix
import pytest
from access_matrix import Side, World, user_id

from site_content.integrations import generation
from site_content.main import app
from site_content.repositories import news
from site_content.schemas.news import NewsIn
from tests.integration.transactions import transaction

OWNED = {"news_id"}

PUBLIC = "Public content, the same for everyone."
NOT_OWNED = {
    "GET /help/pages/{key}": PUBLIC,
    "GET /help/guides/{slug}": PUBLIC,
    "GET /help/legal/{document}": PUBLIC,
}

BODIES = {
    "PUT /superadmin/news/{news_id}": {
        "title": "Matrix",
        "text": "Text.",
        "published_on": "2026-10-01",
    }
}


async def side(kind: str) -> Side:
    post = await transaction(
        news.create, NewsIn(title="Matrix", text="Text.", published_on=date(2026, 10, 1))
    )

    return Side(user_id(kind), {"news_id": str(post.id)})


@pytest.fixture
def world(run, monkeypatch):
    """Generation isn't asked to translate."""

    async def translate_news(news_id):
        return None

    monkeypatch.setattr(generation, "translate_news", translate_news)

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
    found, statuses = run(access_matrix.outcomes(app, route, world, BODIES, {}))

    assert found == access_matrix.expected(route, world, {}), str(statuses)
