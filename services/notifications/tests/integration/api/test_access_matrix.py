"""Every route taking a company's id lets its owners through and refuses another company's
owner, a viewer's change and anyone signed out; superadmin routes refuse everyone else
(access_matrix, .claude/rules/testing.md, Security)."""

from uuid import uuid4

import access_matrix
import pytest
from access_matrix import REFUSED, Side, World, user_id

from notifications.main import app
from notifications.repositories import campaigns, slack
from notifications.services import campaigns as campaign_service
from tests.integration.transactions import transaction

OWNED = {"company_id"}

NOT_OWNED = {
    "GET /unsubscribe/{token}": "An email's unsubscribe link: its token is the secret.",
    "POST /unsubscribe/{token}": "An email's unsubscribe link: its token is the secret.",
}

VALUES = {"document": "terms", "language": "de", "news_id": str(uuid4())}

TEXTS = {"subject": "Matrix", "text": "Matrix.", "button": None}
BODIES = {
    "PUT /slack/kinds": {"kinds": []},
    "PUT /superadmin/campaigns/{campaign_id}": {"kind": "updates", **TEXTS},
    "PUT /superadmin/campaigns/{campaign_id}/texts/{language}": TEXTS,
}

EXCEPTIONS = {
    # Connecting Slack starts its approval: owners and admins only.
    "GET /slack/start": {"viewer": REFUSED},
}


async def side(kind: str) -> Side:
    """A company's owner and viewer, its Slack channel, and a campaign draft."""
    company, owner = str(uuid4()), user_id(kind)
    await transaction(
        slack.connect, company, "Acme", "#hiring", "sealed", "sealed", uuid4().hex, [], owner
    )
    fields = {"kind": "updates", "groups": [], "editors_only": False, "company_ids": []}
    campaign = await transaction(campaigns.create, {**fields, "link": None}, "sam", TEXTS)
    ids = {"company_id": company, "campaign_id": str(campaign.id)}

    return Side(owner, ids, user_id(f"{kind}-viewer"))


@pytest.fixture
def world(run, monkeypatch):
    """Generation isn't asked to translate."""

    async def translate(campaign_id):
        return None

    monkeypatch.setattr(campaign_service.generation, "translate_campaign", translate)

    async def make():
        return World(await side("mine"), await side("theirs"))

    return access_matrix.enter(monkeypatch, run(make()))


def test_every_route_taking_an_id_is_in_the_matrix_or_listed_with_why():
    assert access_matrix.unlisted(app, OWNED, NOT_OWNED) == []


@pytest.mark.parametrize("route", access_matrix.routes(app, OWNED, NOT_OWNED), ids=str)
def test_only_whoever_may_gets_through(route, world, run):
    found, statuses = run(access_matrix.outcomes(app, route, world, BODIES, VALUES))

    assert found == access_matrix.expected(route, world, EXCEPTIONS), str(statuses)
