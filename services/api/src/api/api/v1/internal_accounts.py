from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from prepza_common.auth.user import UserEmailIn

from api.api.dependencies import ServiceCaller
from api.repositories import keys, webhook_retries, webhooks

router = APIRouter(prefix="/internal", tags=["internal"], include_in_schema=False)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, caller: ServiceCaller, body: UserEmailIn | None = None) -> None:
    """Library, deleting an account: the keys and web hooks they made go, and their results as a
    candidate waiting to be sent again to companies' web hooks."""
    await keys.remove_user(user_id)
    await webhooks.remove_user(user_id)

    if body is not None:
        await webhook_retries.remove_email(body.email)


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, caller: ServiceCaller) -> dict:
    """Library, for "Download my data": the keys (names only) and web hooks they made."""
    return jsonable_encoder(
        {
            "api_keys": [
                {"company_id": key.company_id, "name": key.name, "at": key.created_at}
                for key in await keys.of_user(user_id)
            ],
            "webhooks": [
                {"company_id": hook.company_id, "url": hook.url, "at": hook.created_at}
                for hook in await webhooks.of_user(user_id)
            ],
        }
    )
