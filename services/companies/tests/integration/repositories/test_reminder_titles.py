from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from companies.core.db import Session
from companies.models.outbox import OutboxEvent
from companies.repositories import interviews, invites, reminders
from tests.integration.repositories.test_invites import interview
from tests.integration.transactions import transaction


def test_a_reminder_waits_for_its_interviews_title_and_then_names_it(run):
    async def scenario():
        found = await interview()
        invite, _ = await transaction(
            invites.upsert, found.id, "tia@example.com", "Backend", "Acme", "en"
        )
        later = datetime.now(UTC) + timedelta(seconds=1)
        await transaction(reminders.remind_unstarted, later)

        async def sent():
            async with Session() as session:
                return list(
                    await session.scalars(
                        select(OutboxEvent.data).where(
                            OutboxEvent.event_type == "candidate.reminded",
                            OutboxEvent.data["invite_id"].astext == str(invite.id),
                        )
                    )
                )

        untitled = await sent()
        await transaction(interviews.set_title, found.id, "Backend")
        await transaction(reminders.remind_unstarted, later)

        return untitled, await sent()

    untitled, titled = run(scenario())

    assert untitled == []
    assert [event["title"] for event in titled] == ["Backend"]
