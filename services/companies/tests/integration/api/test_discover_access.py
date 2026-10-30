"""An interview's Discover tab is refused to a company that never topped up and to another
company's member; a paying company's member gets the people rounds lists (services/discover.py).
The matrix (test_access_matrix.py) checks roles with both companies paying."""

from uuid import uuid4

import access_matrix
import httpx
import pytest
from access_matrix import HOST, World

from companies.integrations import billing, library, rounds
from companies.main import app
from tests.integration.api.test_access_matrix import side

PERSON = {
    "user_id": "ann-open",
    "name": "Ann Lee",
    "linkedin_url": "https://www.linkedin.com/in/ann-lee",
    "results": [{"topic_title": "Python", "score": 80, "finished_at": "2026-10-29T10:00:00Z"}],
}


@pytest.fixture
def world(run, monkeypatch):
    """Mine never topped up; theirs did."""
    found = run(_world())
    access_matrix.enter(monkeypatch, found)
    paying = found.theirs.ids["company_id"]

    async def company_paid(company_id):
        return str(company_id) == paying

    async def practice_topics(set_id):
        return [str(uuid4())]

    async def offer_matches(topic_ids, offset, limit):
        return [PERSON]

    monkeypatch.setattr(billing, "company_paid", company_paid)
    monkeypatch.setattr(library, "practice_topics", practice_topics)
    monkeypatch.setattr(rounds, "offer_matches", offer_matches)

    return found


async def _world():
    return World(await side(f"unpaid-{uuid4().hex[:6]}"), await side(f"paid-{uuid4().hex[:6]}"))


async def calls(world: World) -> dict:
    mine, theirs = world.mine, world.theirs
    asked = {
        "unpaid owner": ("GET", mine.user, mine.ids["interview_id"]),
        "unpaid owner invites": ("POST", mine.user, mine.ids["interview_id"]),
        "other company's owner": ("GET", theirs.user, mine.ids["interview_id"]),
        "other company's owner invites": ("POST", theirs.user, mine.ids["interview_id"]),
        "paying owner": ("GET", theirs.user, theirs.ids["interview_id"]),
    }
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    answers = {}

    async with httpx.AsyncClient(transport=transport, base_url=f"http://{HOST}") as client:
        for name, (method, user, interview_id) in asked.items():
            url = f"/interviews/{interview_id}/discover"
            url += "/ann-open/invite" if method == "POST" else ""
            response = await client.request(
                method, url, headers={"Authorization": f"Bearer {user}"}
            )
            answers[name] = (response.status_code, response.json())

    return answers


def test_only_a_paying_companys_members_see_the_people_open_to_offers(world, run):
    answers = run(calls(world))

    unpaid = (
        403,
        {
            "detail": "Only companies that have topped up can see people open to offers.",
            "code": "discover_unpaid",
        },
    )
    assert answers["unpaid owner"] == unpaid
    assert answers["unpaid owner invites"] == unpaid
    assert answers["other company's owner"][0] == 404
    assert answers["other company's owner invites"][0] == 404
    assert answers["paying owner"] == (
        200,
        [{**{k: v for k, v in PERSON.items() if k != "user_id"}, "id": "ann-open"}],
    )
