from contextvars import ContextVar
from typing import Annotated

from fastapi import Depends, Header
from prepza_common.auth.service_auth import callee_secret, issue_token, service_caller, token_claims

from app.config.settings import settings
from app.constants.audit import VIAS

SERVICE_NAME = "companies"


def service_token(callee: str) -> str:
    """A token for calling `callee` (library, rounds, ...), signed with that service's key."""
    return issue_token(SERVICE_NAME, callee, callee_secret(callee))


# Calls to this service, signed with its own key.
ServiceCaller = service_caller(settings.service_secret, SERVICE_NAME)


def assistant_claims(token: str | None) -> dict:
    """What a user's request came through, when not the app itself, from its X-Assistant header:
    a service token the assistant signed for this service, issued as the in-app assistant
    ("assistant") or an AI app connected over MCP ("mcp"); for an AI agent signed in with an API
    key, also the key's company and id. Empty for a missing or forged one."""
    claims = token_claims(token, settings.service_secret, SERVICE_NAME) if token else None

    return claims if claims and claims["iss"] in VIAS else {}


def via_of(token: str | None) -> str | None:
    return assistant_claims(token).get("iss")


# What the request being handled came through, for the access checks (services/access.py), and
# for an API key's request the one company it may reach and the key, as text (the audit log
# records the key).
REQUEST_VIA: ContextVar[str | None] = ContextVar("request_via", default=None)
REQUEST_COMPANY: ContextVar[str | None] = ContextVar("request_company", default=None)
REQUEST_KEY: ContextVar[str | None] = ContextVar("request_key", default=None)


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
