import json
import uuid

import httpx
import pytest
from sqlalchemy import func, select
from testee_common.auth.auth import current_user
from testee_common.auth.user import User
from testee_common.http import http

from notifications.config import settings
from notifications.core.db import Session
from notifications.helpers.unsubscribe import address_hash
from notifications.main import app
from notifications.models.opt_outs import CandidateOptOut
from notifications.repositories import opt_outs
from tests.integration.factories import api
from tests.integration.transactions import transaction


@pytest.fixture
def acme(monkeypatch):
    """Companies at the HTTP boundary: Acme invited the address; the superadmin Sam signs in."""
    company = str(uuid.uuid4())
    monkeypatch.setenv("SUPERADMIN_EMAILS", "sam@testee.dev")
    monkeypatch.setattr(settings, "companies_url", "http://companies")

    def answer(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/internal/invites/companies":
            return httpx.Response(200, json={"company_ids": [company]})

        ids = json.loads(request.content)["company_ids"]

        return httpx.Response(
            200, json={"companies": [{"id": id, "name": "Acme", "members": []} for id in ids]}
        )

    monkeypatch.setattr(
        http, "get_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(answer))
    )
    app.dependency_overrides[current_user] = lambda: User(
        uid="sam",
        email="sam@testee.dev",
        email_verified=True,
        sign_in_provider="google.com",
    )
    yield company

    app.dependency_overrides.clear()


def test_stopping_twice_stores_one_stop_and_lifting_it_keeps_the_candidates_own(run, acme):
    """The superadmin's stop is lifted; the reminders the candidate stopped from an email's link
    stay stopped, and a stop the candidate made themselves can't be lifted there."""
    email = f"dee-{uuid.uuid4()}@example.com"
    address = address_hash(email)

    async def count():
        async with Session() as session:
            return await session.scalar(
                select(func.count()).where(
                    CandidateOptOut.address == address, CandidateOptOut.company_id == acme
                )
            )

    async def scenario():
        # One invite's reminders, stopped from an email's link.
        await transaction(opt_outs.add, address, acme, str(uuid.uuid4()))

        async with api() as client:
            body = {"email": email.upper(), "company_id": acme, "stopped": True}
            stops = [(await client.put("/superadmin/candidate-opt-outs", json=body)).json()]
            stops.append((await client.put("/superadmin/candidate-opt-outs", json=body)).json())
            stored = await count()
            body["stopped"] = False

            for _ in range(2):
                through = await client.put("/superadmin/candidate-opt-outs", json=body)

            # The candidate stops every email themselves; the superadmin can't lift that.
            await transaction(opt_outs.add, address, acme)
            kept = await client.put("/superadmin/candidate-opt-outs", json=body)

        return stops, stored, through.json(), kept.json(), await count()

    stops, stored, through, kept, left = run(scenario())

    stopped = {
        "company_id": acme,
        "name": "Acme",
        "stopped": True,
        "stopped_by_admin": True,
        "stopped_reminders": 1,
    }
    assert stops == [{"companies": [stopped]}, {"companies": [stopped]}]
    assert stored == 2
    assert through == {"companies": [{**stopped, "stopped": False, "stopped_by_admin": False}]}
    assert kept == {"companies": [{**stopped, "stopped_by_admin": False}]}
    assert left == 2
