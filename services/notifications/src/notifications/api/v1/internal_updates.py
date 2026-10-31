from fastapi import APIRouter
from testee_common.auth.service_auth import only_from
from testee_common.config.constants import UPDATES_CALLER

from notifications.api.dependencies import ServiceCaller
from notifications.core.db import Session
from notifications.repositories import updates
from notifications.schemas.notifications import UpdateOut, UpdatesIn, UpdatesOut

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/updates")
async def company_updates(body: UpdatesIn, caller: ServiceCaller) -> UpdatesOut:
    """The assistant, for its get_updates tool: what reached these companies' bells between two
    times, newest first. Reading them marks nothing as seen."""
    only_from(caller, UPDATES_CALLER)
    ids = [str(company_id) for company_id in body.company_ids]
    rows = []

    if ids:
        async with Session() as session:
            rows = await updates.of_companies(session, ids, body.since, body.until)

    return UpdatesOut(items=[UpdateOut.model_validate(row) for row in rows])
