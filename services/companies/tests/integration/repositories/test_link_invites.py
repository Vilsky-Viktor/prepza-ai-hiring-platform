from sqlalchemy import select

from companies.core.db import Session
from companies.models.outbox import OutboxEvent
from companies.repositories import interviews, link_invites
from companies.schemas.interviews import InterviewSettings
from tests.integration.repositories.test_invites import interview
from tests.integration.transactions import transaction

DETAILS = {"title": "Backend", "company": "Acme", "language": "en", "logo_path": None}


def test_a_new_link_candidate_is_emailed_their_own_link_once(run):
    async def scenario():
        found = await interview()
        invite = await transaction(
            link_invites.for_link, found.id, "Ann@Example.com", details=DETAILS
        )
        # Starting again, or a second request at the same moment, sends nothing more.
        await transaction(link_invites.for_link, found.id, "ann@example.com", details=DETAILS)

        async with Session() as session:
            sent = list(
                await session.scalars(
                    select(OutboxEvent.data).where(
                        OutboxEvent.event_type == "candidate.joined",
                        OutboxEvent.data["invite_id"].astext == str(invite.id),
                    )
                )
            )

        return found, invite, sent

    found, invite, sent = run(scenario())

    assert sent == [
        {
            "invite_id": str(invite.id),
            "company_id": str(found.company_id),
            "email": "ann@example.com",
            "token": invite.token,
            **DETAILS,
        }
    ]


def test_a_link_finds_its_test_and_makes_one_invite_per_email_without_an_email(run):
    async def scenario():
        found = await interview()
        await transaction(interviews.set_link, found.id, "link-code")
        linked = await transaction(interviews.get_by_link, "link-code")
        first = await transaction(link_invites.for_link, found.id, "Ann@Example.com")
        again = await transaction(link_invites.for_link, found.id, "ann@example.com")
        await transaction(interviews.set_link, found.id, None)

        return (
            linked.id == found.id,
            first.id == again.id,
            first,
            await transaction(interviews.get_by_link, "link-code"),
        )

    same_test, same_invite, invite, after_off = run(scenario())

    assert same_test and same_invite
    assert (invite.email, invite.status) == ("ann@example.com", "invited")
    # Turned off, the link finds nothing.
    assert after_off is None


def test_marking_a_test_hired_turns_its_link_off(run):
    async def scenario():
        found = await interview()
        await transaction(interviews.set_link, found.id, "hired-code")
        await transaction(interviews.update_settings, found.id, InterviewSettings(hired=False))
        kept = await transaction(interviews.get_by_link, "hired-code")
        await transaction(interviews.update_settings, found.id, InterviewSettings(hired=True))

        return kept, await transaction(interviews.get_by_link, "hired-code")

    kept, after_hired = run(scenario())

    assert kept is not None
    assert after_hired is None
