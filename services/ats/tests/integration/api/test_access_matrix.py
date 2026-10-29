"""Every route taking a company's id or one of its job links' lets its owners through and
refuses another company's owner, a viewer's change and anyone signed out (access_matrix,
.claude/rules/testing.md, Security)."""

from uuid import uuid4

import access_matrix
import internal_matrix
import pytest
from access_matrix import REFUSED, Side, World, user_id

from ats.constants.ats import AtsProvider
from ats.main import app
from ats.repositories import ats, ats_links
from tests.integration.transactions import transaction

OWNED = {"company_id", "link_id"}

# An ATS sends these, signed with the company's own key, which the route checks.
SIGNED = "An ATS's web hook: its signature with the company's key is checked."
NOT_OWNED = {
    "POST /webhooks/workable/{link_id}": SIGNED,
    "POST /webhooks/greenhouse/{connection_id}": SIGNED,
    "POST /webhooks/teamtailor/{connection_id}": SIGNED,
    "POST /webhooks/recruitee/{connection_id}": SIGNED,
    "POST /webhooks/breezy/{connection_id}": SIGNED,
}

# The ATS's own jobs are read from it, through the company's connection.
VALUES = {"provider": AtsProvider.RECRUITEE, "job_id": "A1"}

BODIES = {
    "POST /links": {
        "provider": AtsProvider.RECRUITEE,
        "job_id": "A1",
        "stage_id": "assessment",
        "interview_id": str(uuid4()),
    },
}

# Reading the ATS's jobs uses the company's connection: owners and admins, who link them.
EDITORS = {"viewer": REFUSED}
EXCEPTIONS = {
    "GET /{provider}/jobs": EDITORS,
    "GET /{provider}/jobs/{job_id}/stages": EDITORS,
    "GET /{provider}/jobs/{job_id}/text": EDITORS,
    "GET /{provider}/webhook": EDITORS,
}


async def side(kind: str) -> Side:
    """A company's owner and viewer, its Recruitee connection and a job linked to a test."""
    owner, company = user_id(kind), uuid4()
    await transaction(ats.connect, company, AtsProvider.RECRUITEE, "acme", "sealed", owner)
    connection = await transaction(ats.connection, company, AtsProvider.RECRUITEE)
    job, stage = {"id": "A1", "name": "Accountant"}, {"id": "assessment", "name": "Assessment"}
    link = await transaction(ats_links.add_link, company, connection.id, uuid4(), job, stage, owner)
    ids = {"company_id": str(company), "link_id": str(link)}

    return Side(owner, ids, user_id(f"{kind}-viewer"))


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

    assert found == access_matrix.expected(route, world, EXCEPTIONS), str(statuses)
