import uuid

from sqlalchemy import update

from companies.constants.invites import InviteStatus
from companies.core.db import Session
from companies.models.invites import CandidateInvite
from companies.repositories import companies, credit_invites, interviews, invites


async def interview_of(company, title: str):
    found = await interviews.create(company.id, uuid.uuid4(), "en", 60)
    await interviews.set_title(found.id, title)

    return found


async def invite(found, email, status=InviteStatus.INVITED, hold_key=None):
    """An invite in this status; without a hold key, like invites made before they had one."""
    created, _ = await invites.upsert(found.id, email, "", "Acme", "en", hold_key=hold_key)

    async with Session() as session:
        await session.execute(
            update(CandidateInvite).where(CandidateInvite.id == created.id).values(status=status)
        )
        await session.commit()

    return created


def test_only_open_invites_hold_credits_newest_first(run):
    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        other = await companies.create(f"Other {uuid.uuid4()}", "owner", "owner@example.com")
        backend = await interview_of(company, "Backend")
        frontend = await interview_of(company, "Frontend")
        # Invited in this order, so newest first is cleo, ben, ann.
        await invite(backend, "ann@example.com", hold_key="h-ann")
        await invite(frontend, "ben@example.com", InviteStatus.UNDELIVERED, "h-ben")
        await invite(frontend, "cleo@example.com", InviteStatus.IN_PROCESS, "h-cleo")
        # Charged, given back, or gone: nothing held.
        await invite(backend, "dan@example.com", InviteStatus.FINISHED, "h-dan")
        await invite(backend, "eve@example.com", InviteStatus.EXPIRED, "h-eve")
        await invite(backend, "fay@example.com", InviteStatus.DELETED, "h-fay")
        # Another company's candidate.
        await invite(await interview_of(other, "Elsewhere"), "gus@example.com")

        return (
            await credit_invites.count_holding(company.id),
            await credit_invites.holding(company.id, 0, 2),
            await credit_invites.holding(company.id, 2, 2),
        )

    count, first, second = run(scenario())

    assert count == 3
    assert [(row.email, interview.title) for row, interview in first + second] == [
        ("cleo@example.com", "Frontend"),
        ("ben@example.com", "Frontend"),
        ("ann@example.com", "Backend"),
    ]


def test_history_keys_find_only_the_companys_own_invites(run):
    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        other = await companies.create(f"Other {uuid.uuid4()}", "owner", "owner@example.com")
        backend = await interview_of(company, "Backend")
        elsewhere = await interview_of(other, "Elsewhere")
        await invite(backend, "ann@example.com", InviteStatus.FINISHED, "h-ann")
        await invite(backend, "cid@example.com", InviteStatus.DELETED, "h-cid")
        await invite(elsewhere, "dan@example.com", InviteStatus.FINISHED, "h-dan")
        keys = ["h-ann", "h-cid", "h-dan", "h-unknown"]

        return await credit_invites.by_hold_keys(company.id, keys)

    found = run(scenario())

    # A deleted candidate, another company's and an unknown key aren't found.
    assert {key: (row.email, interview.title) for key, (row, interview) in found.items()} == {
        "h-ann": ("ann@example.com", "Backend"),
    }


def test_no_keys_ask_nothing(run):
    assert run(credit_invites.by_hold_keys(uuid.uuid4(), [])) == {}
