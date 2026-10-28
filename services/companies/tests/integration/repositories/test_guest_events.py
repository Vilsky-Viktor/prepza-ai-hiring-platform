"""Deleting a guest invite, however it goes, tells library to delete the guest's own sign-in and
rows (guests.deleted), in the same transaction; an invite with a sign-in of its own doesn't."""

import uuid

import pytest
from sqlalchemy import select

from companies.core.db import Session
from companies.models.outbox import OutboxEvent
from companies.repositories import accounts, companies, interviews, invites


async def announced() -> set[str]:
    async with Session() as session:
        rows = await session.scalars(
            select(OutboxEvent.data).where(OutboxEvent.event_type == "guests.deleted")
        )

        return {user_id for data in rows for user_id in data["user_ids"]}


async def guest_and_member_invites():
    company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
    interview = await interviews.create(company.id, uuid.uuid4(), "en", 60)
    guest, _ = await invites.upsert(
        interview.id, f"g-{uuid.uuid4()}@example.com", "Backend", "Acme", "en", sign_in=False
    )
    member, _ = await invites.upsert(
        interview.id, f"m-{uuid.uuid4()}@example.com", "Backend", "Acme", "en"
    )

    return company, interview, guest, member


async def remove_one(company, interview, guest, member):
    await invites.remove(guest, company.id)
    await invites.remove(member, company.id)


async def by_retention(company, interview, guest, member):
    await accounts.delete_invites([guest.id, member.id])


async def with_the_interview(company, interview, guest, member):
    await interviews.remove(interview.id)


async def with_the_company(company, interview, guest, member):
    await companies.delete(company.id)


@pytest.mark.parametrize("delete", [remove_one, by_retention, with_the_interview, with_the_company])
def test_a_deleted_guest_invite_announces_its_guest_and_no_one_else(run, delete):
    async def scenario():
        company, interview, guest, member = await guest_and_member_invites()
        await delete(company, interview, guest, member)

        return guest, member, await announced()

    guest, member, user_ids = run(scenario())

    assert f"guest-{guest.id}" in user_ids
    assert f"guest-{member.id}" not in user_ids
