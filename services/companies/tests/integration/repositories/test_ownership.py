import uuid

from sqlalchemy import select

from companies.core.db import Session
from companies.models.outbox import OutboxEvent
from companies.repositories import accounts, companies, members


async def roles(company_id) -> dict[str, str]:
    return {row.user_id: row.role for row in await members.list_for_company(company_id, 0, 10)}


def test_the_owner_hands_the_company_to_a_joined_admin_once(run):
    ann, bob = f"ann-{uuid.uuid4()}", f"bob-{uuid.uuid4()}"

    async def scenario():
        company = await companies.create(f"Owned {uuid.uuid4()}", ann, "ann@example.com")
        invited = await members.add(company.id, "bob@example.com", "admin", {})
        await members.accept(invited, company, bob)
        listed = await members.list_for_company(company.id, 0, 10)
        owner = next(row for row in listed if row.user_id == ann)
        admin = next(row for row in listed if row.user_id == bob)

        moved = await members.transfer_ownership(company, owner, admin)
        # The same transfer again (a double click): Ann isn't the owner any more.
        again = await members.transfer_ownership(company, owner, admin)
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

        await companies.delete(company.id)

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
        alone = await companies.create(f"Alone {uuid.uuid4()}", ann, "ann@example.com")
        shared = await companies.create(f"Shared {uuid.uuid4()}", ann, "ann@example.com")
        invited = await members.add(shared.id, "bob@example.com", "viewer", {})
        await members.accept(invited, shared, bob)
        # Only invited: not joined, so it doesn't count.
        await members.add(alone.id, "cid@example.com", "admin", {})
        found = {company.id: others for company, others in await accounts.owned(ann)}

        for company in (alone, shared):
            await companies.delete(company.id)

        return found, alone.id, shared.id

    found, alone, shared = run(scenario())

    assert found == {alone: False, shared: True}
