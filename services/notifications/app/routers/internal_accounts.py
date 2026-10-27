from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from prepza_common.auth.user import UserEmailIn
from prepza_common.events.notifications import Recipient

from app.schemas.notifications import NotificationOut
from app.service_auth import ServiceCaller
from app.services import slack as slack_service
from app.storage import bulk_recipients, notifications, sent_emails, slack

router = APIRouter(prefix="/internal", tags=["internal"])


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, body: UserEmailIn, caller: ServiceCaller) -> None:
    """Library, deleting an account: the user's own notifications go, and companies'
    notifications about them as a candidate (their email and grade), and owners' notifications
    that they joined a company (their email); the Slack channels they
    connected stay with their companies, without their id, and each company is told they need
    reconnecting. The log of digests and reminders
    sent to them goes too, and their rows in bulk sends (legal notices, campaigns)."""
    await notifications.remove_user(user_id)
    await sent_emails.remove_user(user_id)
    await bulk_recipients.remove_user(user_id)
    await notifications.remove_candidate(body.email)
    await notifications.remove_member(body.email)

    for company_id in await slack.forget_maker(user_id):
        await slack_service.stopped(company_id)


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, caller: ServiceCaller) -> dict:
    """Library, for "Download my data": the user's own notifications and the Slack channels
    they connected."""
    items = await notifications.latest([(Recipient.USER, user_id)], limit=None)

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
                for row in await slack.made_by(user_id)
            ],
        }
    )
