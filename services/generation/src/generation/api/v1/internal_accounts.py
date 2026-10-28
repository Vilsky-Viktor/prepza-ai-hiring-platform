from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder

from generation.api.dependencies import ServiceCaller
from generation.core.db import Session
from generation.repositories import accounts
from generation.services.accounts import delete_user as delete_account

router = APIRouter(prefix="/internal", tags=["internal"])


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, caller: ServiceCaller) -> None:
    """Part of deleting an account (accounts coordinates it); safe to repeat."""
    await delete_account(user_id)


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, caller: ServiceCaller) -> dict:
    async with Session() as session:
        found = await accounts.export(session, user_id)

    return jsonable_encoder({"generations": found})
