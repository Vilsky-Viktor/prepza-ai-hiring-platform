"""Library's old account routes: users' addresses, ids, email settings and accounts now live in
the accounts service, which the callers call. Kept one release (microservices.md, 3) for a
caller still running the version before, each answering what accounts answers."""

from fastapi import APIRouter, Request, Response

from library.api.dependencies import ServiceCaller
from library.integrations.accounts_routes import forward

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/users/ids")
async def user_ids(request: Request, caller: ServiceCaller) -> Response:
    return await forward(request)


@router.post("/users/with-setting")
async def users_with_setting(request: Request, caller: ServiceCaller) -> Response:
    return await forward(request)


@router.post("/users/email-recipients")
async def email_recipients(request: Request, caller: ServiceCaller) -> Response:
    return await forward(request)


@router.post("/users/{user_id}/unsubscribe")
async def unsubscribe(user_id: str, request: Request, caller: ServiceCaller) -> Response:
    return await forward(request)


@router.get("/accounts/{user_id}")
async def get_account(user_id: str, request: Request, caller: ServiceCaller) -> Response:
    return await forward(request)


@router.post("/accounts/lookup")
async def look_up(request: Request, caller: ServiceCaller) -> Response:
    return await forward(request)
