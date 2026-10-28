"""Rounds' old internal content route: what the assistant's help chat answers from now lives in
the site service, which the assistant calls. Kept one release (microservices.md, 3) for an
assistant still running the version before, answering what site answers."""

from fastapi import APIRouter, Request, Response

from rounds.api.dependencies import ServiceCaller
from rounds.integrations.site_routes import forward

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/help/knowledge")
async def knowledge(request: Request, caller: ServiceCaller) -> Response:
    return await forward(request)
