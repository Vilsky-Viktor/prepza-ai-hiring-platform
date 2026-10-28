"""Interview lists read a generation's outcome from companies' own table; only an interview's
own page asks generation, once, and shows what companies knows when generation is down."""

import asyncio
import uuid
from datetime import UTC, datetime

import httpx
import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User

from companies.main import app
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.repositories import candidates, companies, interview_generations, interviews
from companies.services import interview_views as helpers

COMPANY_ID = uuid.uuid4()


def interview(failed=False):
    return Interview(
        id=uuid.uuid4(),
        company_id=COMPANY_ID,
        generation_id=uuid.uuid4(),
        set_id=None,
        title=None,
        question_seconds=60,
        hired=False,
        pass_mark=70,
        link_token=None,
        generation_failed=failed,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def stored(monkeypatch):
    """Changes the helpers save: (interview id, failed)."""
    saved = []

    async def set_generation_failed(session, interview_id, failed):
        saved.append((interview_id, failed))

    monkeypatch.setattr(interview_generations, "set_generation_failed", set_generation_failed)

    return saved


def generation_answers(monkeypatch, answer):
    """Generation answers each interview's lookup with `answer` (raised when an exception)."""
    asked = []

    async def get(generation_id, company_id):
        asked.append(generation_id)

        if isinstance(answer, Exception):
            raise answer

        return answer

    monkeypatch.setattr(helpers.generation_api, "get", get)

    return asked


def test_listing_never_asks_generation_and_shows_the_stored_failure(client, monkeypatch):
    rows = [interview(), interview(failed=True)]
    asked = generation_answers(monkeypatch, httpx.ConnectError("generation is down"))
    company = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC))
    company.members = [
        Member(company_id=COMPANY_ID, user_id="bob", invited_email="bob@example.com", role="admin")
    ]

    async def found(session, _company_id):
        return company

    async def listed(session, company_id, offset, limit, **filters):
        return rows

    async def counts(session, ids):
        return {}

    monkeypatch.setattr(companies, "get", found)
    monkeypatch.setattr(interviews, "list_for_company", listed)
    monkeypatch.setattr(candidates, "counts", counts)
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True, name="bob"
    )

    response = client.get(f"/interviews?company_id={COMPANY_ID}")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert [item["generation_failed"] for item in response.json()] == [False, True]
    assert asked == []


def test_an_interviews_page_learns_of_a_failure_generation_reports(monkeypatch, stored):
    found = interview()
    generation_answers(monkeypatch, {"status": "failed", "preparation_id": None})

    asyncio.run(helpers.attach_set(found))

    assert found.generation_failed is True
    assert stored == [(found.id, True)]


def test_a_failure_retried_elsewhere_is_cleared_and_an_unchanged_one_not_saved(monkeypatch, stored):
    retried, running = interview(failed=True), interview()
    generation_answers(monkeypatch, {"status": "running", "preparation_id": None})

    asyncio.run(helpers.attach_set(retried))
    asyncio.run(helpers.attach_set(running))

    assert (retried.generation_failed, running.generation_failed) == (False, False)
    assert stored == [(retried.id, False)]


def test_with_generation_down_an_interviews_page_shows_what_companies_knows(monkeypatch, stored):
    found = interview(failed=True)
    generation_answers(monkeypatch, httpx.ConnectError("generation is down"))

    assert asyncio.run(helpers.attach_set_if_reachable(found)) is found
    assert (found.set_id, found.generation_failed) == (None, True)
    assert stored == []
