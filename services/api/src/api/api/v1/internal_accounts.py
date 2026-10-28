from fastapi import APIRouter, status
from prepza_common.auth.user import UserEmailIn

from api.api.dependencies import ServiceCaller
from api.services import accounts

router = APIRouter(prefix="/internal", tags=["internal"], include_in_schema=False)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, caller: ServiceCaller, body: UserEmailIn | None = None) -> None:
    """Accounts, deleting an account: the keys and web hooks they made go, and their results as a
    candidate waiting to be sent again to companies' web hooks."""
    await accounts.remove_user(user_id, body.email if body is not None else None)


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, caller: ServiceCaller) -> dict:
    """Accounts, for "Download my data": the keys (names only) and web hooks they made."""
    return await accounts.export_user(user_id)
