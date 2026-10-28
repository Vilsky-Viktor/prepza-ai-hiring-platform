# What other services ask of notifications about a user's account or a company: deleting them,
# and a user's data export.
from datetime import UTC, datetime

from fastapi.encoders import jsonable_encoder
from prepza_common.events.notifications import Recipient

from notifications.core.db import Session
from notifications.repositories import bulk_recipients, notifications, opt_outs, sent_emails, slack
from notifications.schemas.notifications import NotificationOut
from notifications.services import slack as slack_service


async def remove_user(user_id: str, email: str) -> None:
    """The user's own notifications go, and companies' notifications about them as a candidate
    (their email and grade), and owners' notifications that they joined a company (their email);
    the Slack channels they connected stay with their companies, without their id. The log of
    digests and reminders sent to them goes too, and their rows in bulk sends. All of it is one
    save; then each company whose channel stopped working is told it needs reconnecting."""
    async with Session.begin() as session:
        await notifications.remove_user(session, user_id)
        await sent_emails.remove_user(session, user_id)
        await bulk_recipients.remove_user(session, user_id)
        await notifications.remove_candidate(session, email)
        await notifications.remove_member(session, email)
        stopped = await slack.forget_maker(session, user_id)

    for company_id in stopped:
        await slack_service.stopped(company_id)


async def export(user_id: str) -> dict:
    """The user's own notifications and the Slack channels they connected."""
    async with Session() as session:
        items = await notifications.latest(session, [(Recipient.USER, user_id)], limit=None)
        channels = await slack.made_by(session, user_id)

    return jsonable_encoder(
        {
            "notifications": [NotificationOut.model_validate(item) for item in items],
            "slack_channels": [
                {
                    "company_id": row.company_id,
                    "team": row.team,
                    "channel": row.channel,
                    "at": row.created_at,
                }
                for row in channels
            ],
        }
    )


async def remove_company(company_id: str) -> None:
    """A deleted company's notifications go (and it gets none after) with its candidates'
    opt-outs, in one save; then its Slack channel, and prepza's app unless another company uses
    it. Safe to repeat."""
    async with Session.begin() as session:
        await notifications.remove_company(session, company_id, datetime.now(UTC))
        await opt_outs.remove_company(session, company_id)

    await slack_service.disconnect(company_id)
