"""Every route taking the id of a company's API key or web hook lets its owners through and
refuses another company's owner, a viewer's change and anyone signed out (access_matrix,
.claude/rules/testing.md, Security)."""

from uuid import uuid4

import access_matrix
import internal_matrix
import pytest
from access_matrix import Side, World, user_id

from api.main import app
from api.repositories import keys, webhooks
from tests.integration.transactions import transaction

OWNED = {"company_id", "key_id", "webhook_id"}

# The public API's routes take a key, not a signed-in user: the key's company goes to
# companies, whose /internal routes give only that company's interviews and candidates
# (interview_views.company_interview, candidate_changes.company_candidate).
PUBLIC_API = "Public API: companies scopes the id to the key's company."
NOT_OWNED = {
    "GET /interviews/{interview_id}": PUBLIC_API,
    "GET /interviews/{interview_id}/candidates": PUBLIC_API,
    "GET /interviews/{interview_id}/candidates/{candidate_id}": PUBLIC_API,
    "POST /interviews/{interview_id}/candidates": PUBLIC_API,
    "PATCH /interviews/{interview_id}/candidates/{candidate_id}": PUBLIC_API,
    "DELETE /interviews/{interview_id}/candidates/{candidate_id}": PUBLIC_API,
    "POST /interviews/{interview_id}/candidates/{candidate_id}/resend": PUBLIC_API,
    "GET /interviews/{interview_id}/notes": PUBLIC_API,
    "POST /interviews/{interview_id}/notes": PUBLIC_API,
}

BODIES = {
    "PATCH /manage/keys/{key_id}": {"permissions": ["interviews:read"]},
    "PUT /manage/keys/{key_id}/allowed-ips": {"allowed_ips": []},
}


async def side(kind: str) -> Side:
    """A company's owner and viewer, with a key and a web hook."""
    owner, company = user_id(kind), uuid4()
    key = await transaction(
        keys.add,
        company,
        "Matrix",
        "te_m",
        uuid4().hex * 2,
        owner,
        None,
        ["interviews:read"],
        [],
        10,
    )
    hook = await transaction(webhooks.add, company, "https://a.example/x", "sealed", owner, 10)
    ids = {"company_id": company, "key_id": key.id, "webhook_id": hook.id}

    return Side(owner, {name: str(value) for name, value in ids.items()}, user_id(f"{kind}-viewer"))


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
    found, statuses = run(access_matrix.outcomes(app, route, world, BODIES, {}))

    assert found == access_matrix.expected(route, world, {}), str(statuses)
