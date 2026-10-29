from fastapi import APIRouter

from api.api.dependencies import ServiceCaller
from api.services import accounts

router = APIRouter(prefix="/internal", tags=["internal"], include_in_schema=False)


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, caller: ServiceCaller) -> dict:
    """Accounts, for "Download my data": the keys (names only) and web hooks they made."""
    return await accounts.export_user(user_id)
