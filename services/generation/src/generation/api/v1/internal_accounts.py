from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder

from generation.api.dependencies import ServiceCaller
from generation.core.db import Session
from generation.repositories import accounts

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, caller: ServiceCaller) -> dict:
    async with Session() as session:
        found = await accounts.export(session, user_id)

    return jsonable_encoder({"generations": found})
