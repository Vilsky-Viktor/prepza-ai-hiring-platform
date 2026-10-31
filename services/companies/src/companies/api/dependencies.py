from typing import Annotated

from fastapi import Depends, Header
from testee_common.auth.service_auth import service_caller

from companies.config import settings
from companies.core.security import (
    REQUEST_COMPANY,
    REQUEST_KEY,
    REQUEST_VIA,
    SERVICE_NAME,
    assistant_claims,
    via_of,
)

# Calls to this service, signed with its own key.
ServiceCaller = service_caller(settings.service_secret, SERVICE_NAME)


async def request_via(
    x_assistant: Annotated[str | None, Header(include_in_schema=False)] = None,
) -> str | None:
    return via_of(x_assistant)


async def remember_via(
    x_assistant: Annotated[str | None, Header(include_in_schema=False)] = None,
) -> None:
    """Every request's: run for the whole app, so each access check knows it."""
    claims = assistant_claims(x_assistant)
    REQUEST_VIA.set(claims.get("iss"))
    REQUEST_COMPANY.set(claims.get("company"))
    REQUEST_KEY.set(claims.get("key"))


# What a user's request came through (the assistant or an AI app), for the audit log; None in
# the app itself.
Via = Annotated[str | None, Depends(request_via)]
