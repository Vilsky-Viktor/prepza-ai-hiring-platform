"""Several addresses' invite statuses, read at once (a list of invites)."""

import uuid

from app.constants.invites import InviteStatus
from app.storage import companies, interviews, invites


def test_a_lists_invite_statuses_are_read_at_once(run):
    async def scenario():
        found = await an_interview()
        await invites.upsert(found.id, "ann@example.com", "Backend", "Acme", "en")

        return await invites.statuses_of(found.id, ["ann@example.com", "bob@example.com"])

    assert run(scenario()) == {"ann@example.com": InviteStatus.INVITED}


async def an_interview():
    company = await companies.create(f"Statuses {uuid.uuid4()}", "owner", "owner@example.com")

    return await interviews.create(company.id, uuid.uuid4(), "en", 60)
