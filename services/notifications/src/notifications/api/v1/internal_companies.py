from uuid import UUID

from fastapi import APIRouter
from prepza_common.auth.service_auth import only_from
from prepza_common.config.constants import INTEGRATIONS_CALLER
from prepza_common.http.counts import CountOut

from notifications.api.dependencies import ServiceCaller
from notifications.core.db import Session
from notifications.repositories import slack

router = APIRouter(prefix="/internal/companies", tags=["internal"])


@router.get("/{company_id}/active-count")
async def active_count(company_id: UUID, caller: ServiceCaller) -> CountOut:
    """Companies, for the company's menu: 1 while its Slack channel is connected and working,
    else 0."""
    only_from(caller, INTEGRATIONS_CALLER)

    async with Session() as session:
        found = await slack.connected(session, str(company_id))

    return CountOut(count=int(found is not None))
