from sqlalchemy import select

from companies.core.db import Session
from companies.models.outbox import OutboxEvent
from companies.repositories import link_invites
from tests.integration.repositories.test_invites import interview

DETAILS = {"title": "Backend", "company": "Acme", "language": "en", "logo_path": None}


def test_a_new_link_candidate_is_emailed_their_own_link_once(run):
    async def scenario():
        found = await interview()
        invite = await link_invites.for_link(found.id, "Ann@Example.com", details=DETAILS)
        # Starting again, or a second request at the same moment, sends nothing more.
        await link_invites.for_link(found.id, "ann@example.com", details=DETAILS)

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
