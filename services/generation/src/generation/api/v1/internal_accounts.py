from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder

from generation.api.dependencies import ServiceCaller
from generation.repositories import accounts

router = APIRouter(prefix="/internal", tags=["internal"])


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, caller: ServiceCaller) -> None:
    """Part of deleting an account (library coordinates it); safe to repeat."""
    await accounts.delete_user(user_id)


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, caller: ServiceCaller) -> dict:
    return jsonable_encoder({"generations": await accounts.export(user_id)})
