"""A member's Slack actions reach the company's action log through notifications' outbox,
saved with the change itself; what changes nothing isn't logged."""

from prepza_common.events.audit_actions import AUDIT_RECORDED
from sqlalchemy import select

from app.models.outbox import OutboxEvent
from app.storage import slack as storage
from app.storage.db import Session
from tests.integration.factories import company
from tests.integration.test_slack import connect


async def logged(company_id) -> list[dict]:
    """The company's actions waiting in the outbox for its action log, oldest first."""
    query = (
        select(OutboxEvent.data)
        .where(
            OutboxEvent.event_type == AUDIT_RECORDED,
            OutboxEvent.data["company_id"].astext == company_id,
        )
        .order_by(OutboxEvent.created_at)
    )

    async with Session() as session:
        return list(await session.scalars(query))


def test_a_members_slack_actions_reach_the_action_log_through_the_outbox(run):
    company_id, other = company(), company()

    async def scenario():
        await connect(company_id, user_id="ann")
        await storage.set_kinds(company_id, ["interview_ready"], "bob")
        await storage.remove(company_id, "ann")
        # No channel: nothing changed, nothing logged.
        await storage.set_kinds(other, ["interview_ready"], "bob")
        await storage.remove(other, "bob")

        return await logged(company_id), await logged(other)

    events, none = run(scenario())

    assert [(row["action"], row["user_id"], row["target_label"]) for row in events] == [
        ("slack_connected", "ann", "#hiring"),
        ("slack_notifications_changed", "bob", "#hiring"),
        ("slack_disconnected", "ann", "#hiring"),
    ]
    assert none == []
