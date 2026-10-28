import uuid

from sqlalchemy import select

from companies.core.db import Session
from companies.models.outbox import OutboxEvent
from companies.repositories import accounts, members
from tests.integration import factories
from tests.integration.transactions import transaction


async def roles(company_id) -> dict[str, str]:
    return {
        row.user_id: row.role
        for row in await transaction(members.list_for_company, company_id, 0, 10)
    }


def test_the_owner_hands_the_company_to_a_joined_admin_once(run):
    ann, bob = f"ann-{uuid.uuid4()}", f"bob-{uuid.uuid4()}"

    async def scenario():
        company = await factories.company(f"Owned {uuid.uuid4()}", ann, "ann@example.com")
        invited = await factories.member(company.id, "bob@example.com", "admin", {})
        await factories.accepted(invited, company, bob)
        listed = await transaction(members.list_for_company, company.id, 0, 10)
        owner = next(row for row in listed if row.user_id == ann)
        admin = next(row for row in listed if row.user_id == bob)

        moved = await factories.transferred(company, owner, admin)
        # The same transfer again (a double click): Ann isn't the owner any more.
        again = await factories.transferred(company, owner, admin)
        after = await roles(company.id)

        async with Session() as session:
            told = list(
                await session.scalars(
                    select(OutboxEvent.data).where(
                        OutboxEvent.data["kind"].astext == "ownership_received",
                        OutboxEvent.data["recipient_id"].astext == bob,
                    )
                )
            )

        await factories.deleted(company.id)

        return moved, again, after, told, company

    moved, again, after, told, company = run(scenario())

    assert (moved, again) == (True, False)
    # Never two owners or none.
    assert after == {ann: "admin", bob: "owner"}
    [notice] = told
    assert notice["data"] == {"name": company.name}


def test_an_owners_companies_say_whether_others_joined_them(run):
    ann, bob = f"ann-{uuid.uuid4()}", f"bob-{uuid.uuid4()}"

    async def scenario():
        alone = await factories.company(f"Alone {uuid.uuid4()}", ann, "ann@example.com")
        shared = await factories.company(f"Shared {uuid.uuid4()}", ann, "ann@example.com")
        invited = await factories.member(shared.id, "bob@example.com", "viewer", {})
        await factories.accepted(invited, shared, bob)
        # Only invited: not joined, so it doesn't count.
        await factories.member(alone.id, "cid@example.com", "admin", {})
        found = {company.id: others for company, others in await transaction(accounts.owned, ann)}

        for company in (alone, shared):
            await factories.deleted(company.id)

        return found, alone.id, shared.id

    found, alone, shared = run(scenario())

    assert found == {alone: False, shared: True}
