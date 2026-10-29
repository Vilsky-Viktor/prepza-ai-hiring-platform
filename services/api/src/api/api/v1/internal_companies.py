from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter
from prepza_common.auth.service_auth import only_from
from prepza_common.config.constants import INTEGRATIONS_CALLER
from prepza_common.http.counts import CountOut

from api.api.dependencies import ServiceCaller
from api.core.db import Session
from api.repositories import keys, webhooks

router = APIRouter(prefix="/internal/companies", tags=["internal"], include_in_schema=False)


@router.get("/{company_id}/active-count")
async def active_count(company_id: UUID, caller: ServiceCaller) -> CountOut:
    """Companies, for the company's menu: its API keys that still work and its web hooks that
    get its events."""
    only_from(caller, INTEGRATIONS_CALLER)

    async with Session() as session:
        live = await keys.live_count(session, company_id, datetime.now(UTC))
        working = await webhooks.working_count(session, company_id)

    return CountOut(count=live + working)
