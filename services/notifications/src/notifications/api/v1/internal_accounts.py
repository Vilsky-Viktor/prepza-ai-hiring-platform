from fastapi import APIRouter

from notifications.api.dependencies import ServiceCaller
from notifications.services import accounts

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, caller: ServiceCaller) -> dict:
    """Accounts, for "Download my data": the user's own notifications and the Slack channels
    they connected."""
    return await accounts.export(user_id)
