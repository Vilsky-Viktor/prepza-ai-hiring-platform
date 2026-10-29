"""Every route taking the id of something a company owns lets its owner through and refuses the
owner of another company, a viewer's change and anyone signed out; superadmin routes refuse
everyone else (access_matrix, .claude/rules/testing.md, Security)."""

from uuid import uuid4

import access_matrix
import pytest
from access_matrix import ALLOWED, REFUSED, Side, World, user_id
from sqlalchemy import update

from companies.core.db import Session
from companies.main import app
from companies.models.interviews import Interview
from companies.repositories import interviews, invites, members
from companies.services import generation_steps
from tests.integration import factories
from tests.integration.transactions import transaction

# The parameters naming something a company owns.
OWNED = {"company_id", "interview_id", "invite_id", "member_id", "user_id"}

# Routes taking an id of nothing owned, and why.
NOT_OWNED = {
    "GET /members/invites/{token}": "A team invite's link: its token is the secret.",
    "POST /members/invites/{token}/accept": "A team invite's link: its token is the secret.",
    "GET /invites/{token}": "A candidate's link: its token is the secret.",
    "POST /invites/{token}/guest": "A guest's link: its token is the secret.",
    "POST /invites/{token}/start": "A candidate's link: its token is the secret.",
    "GET /links/{token}": "An interview's open link: its token is the secret.",
    "POST /links/{token}/start": "An interview's open link: its token is the secret.",
    "GET /companies/{company_id}/logo": "Public on purpose (test_route_guards): emails show it.",
}

# Values of the parameters naming nothing this service owns: the question bank's topics and
# questions are library's, which checks them against the interview's set.
VALUES = {"theme": "light", "topic_id": str(uuid4()), "question_id": str(uuid4())}

# Bodies the OpenAPI description alone can't make valid (validators, unique names).
BODIES = {
    "PATCH /companies/{company_id}/name": lambda ids: {"title": f"Matrix {uuid4()}"},
    "PATCH /interviews/{interview_id}/title": {"title": "Matrix"},
    "POST /interviews/{interview_id}/preview": {"pledged": True},
    "PUT /interviews/{interview_id}/candidates/{invite_id}/extra-time": {"extra_time": 25},
    "PUT /companies/{company_id}/brand-colors/{theme}": {"colors": None},
    "PUT /companies/{company_id}/allowed-domains": {"domains": []},
}

OWNER_ONLY = {"viewer": REFUSED}
EXCEPTIONS = {
    # Every member, viewers too, may take their own test as a candidate would.
    "POST /interviews/{interview_id}/preview": {"viewer": ALLOWED},
    # The audit and action logs are the owner's; credits' history, owners' and admins'.
    "GET /companies/{company_id}/audit": OWNER_ONLY,
    "GET /companies/{company_id}/actions": OWNER_ONLY,
    "GET /companies/{company_id}/billing/history": OWNER_ONLY,
    "GET /companies/{company_id}/billing/reserved": OWNER_ONLY,
    # Reports on a question are read where it's fixed: owners and admins.
    "GET /interviews/{interview_id}/questions/{question_id}/reports": OWNER_ONLY,
}


async def pass_human(request, secret):
    return None


async def side(kind: str) -> Side:
    """A company with its owner, a viewer, an interview, a candidate and the viewer's
    membership."""
    owner, viewer = user_id(kind), user_id(f"{kind}-viewer")
    company = await factories.company(f"Matrix {uuid4()}", owner, f"{owner}@example.com")
    member = await transaction(members.add, company.id, f"{viewer}@example.com", "viewer", {})
    await transaction(members.join, member.id, viewer)
    # Generated and ready: both its generation's routes and its questions' have something.
    interview = await transaction(interviews.create, company.id, uuid4(), "en", 60)

    async with Session.begin() as session:
        await session.execute(
            update(Interview).where(Interview.id == interview.id).values(set_id=uuid4())
        )

    candidate, _ = await transaction(
        invites.upsert, interview.id, "candidate@example.com", "Backend", company.name, "en"
    )
    ids = {
        "company_id": company.id,
        "interview_id": interview.id,
        "invite_id": candidate.id,
        "member_id": member.id,
        "user_id": owner,
    }

    return Side(owner, {name: str(value) for name, value in ids.items()}, viewer)


@pytest.fixture
def world(run, monkeypatch):
    """No Turnstile here: the owner's review gets past the person check."""
    monkeypatch.setattr(generation_steps, "require_human", pass_human)

    async def make():
        return World(await side("mine"), await side("theirs"))

    return access_matrix.enter(monkeypatch, run(make()))


def test_every_route_taking_an_id_is_in_the_matrix_or_listed_with_why():
    assert access_matrix.unlisted(app, OWNED, NOT_OWNED) == []


@pytest.mark.parametrize("route", access_matrix.routes(app, OWNED, NOT_OWNED), ids=str)
def test_only_whoever_may_gets_through(route, world, run):
    found, statuses = run(access_matrix.outcomes(app, route, world, BODIES, VALUES))

    assert found == access_matrix.expected(route, world, EXCEPTIONS), str(statuses)
