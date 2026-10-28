from fastapi import APIRouter, status
from prepza_common.auth.user import UserEmailIn

from notifications.api.dependencies import ServiceCaller
from notifications.services import accounts

router = APIRouter(prefix="/internal", tags=["internal"])


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, body: UserEmailIn, caller: ServiceCaller) -> None:
    """Accounts, deleting an account: the user's own notifications go, and companies'
    notifications about them as a candidate (their email and grade), and owners' notifications
    that they joined a company (their email); the Slack channels they
    connected stay with their companies, without their id, and each company is told they need
    reconnecting. The log of digests and reminders
    sent to them goes too, and their rows in bulk sends (legal notices, campaigns)."""
    await accounts.remove_user(user_id, body.email)


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, caller: ServiceCaller) -> dict:
    """Accounts, for "Download my data": the user's own notifications and the Slack channels
    they connected."""
    return await accounts.export(user_id)
