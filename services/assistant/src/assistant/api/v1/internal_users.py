from datetime import UTC, datetime

from fastapi import APIRouter
from prepza_common.auth.service_auth import only_from
from prepza_common.config.constants import INTEGRATIONS_CALLER
from prepza_common.http.counts import CountOut

from assistant.api.dependencies import ServiceCaller
from assistant.core.db import Session
from assistant.repositories import oauth

router = APIRouter(prefix="/internal/users", tags=["internal"])


@router.get("/{user_id}/active-count")
async def active_count(user_id: str, caller: ServiceCaller) -> CountOut:
    """Companies, for a company's menu: the AI apps the user connected, which are theirs, not
    the company's, and still connected."""
    only_from(caller, INTEGRATIONS_CALLER)

    async with Session() as session:
        count = await oauth.connected_app_count(session, user_id, datetime.now(UTC))

    return CountOut(count=count)
