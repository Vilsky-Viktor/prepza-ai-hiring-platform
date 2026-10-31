import json
import logging
import uuid
from datetime import UTC, datetime

import mcp_types as types
from fastapi import HTTPException
from testee_common.ai.secrets_check import SECRET_REMOVED, secret_in
from testee_common.auth.user import User
from testee_common.config.constants import DAY_SECONDS, VIA_MCP
from testee_common.events.analytics import track
from testee_common.i18n.i18n import translate
from testee_common.limits.pause import refuse_if_paused
from testee_common.limits.rate_limit import hit_or_skip

from assistant.config import settings
from assistant.constants.chat import OTHER_COMPANY
from assistant.constants.mcp import (
    ACCOUNT_GONE,
    ACTIVE_KEY,
    EXCLUDED_TOOL,
    KEY_FUNNEL_CLIENT,
    MAX_LOGGED_TOOL_NAME,
    MCP_EXCLUDED,
    MCP_SCOPE,
    MCP_UNLISTED,
    READ_ONLY,
    UPDATE_LANGUAGE,
)
from assistant.constants.tool_calls import UNKNOWN_TOOL
from assistant.constants.updates import GET_UPDATES
from assistant.core.db import Session
from assistant.helpers.arguments import texts_in
from assistant.helpers.mcp_schema import mcp_tool
from assistant.helpers.oauth import funnel_client
from assistant.integrations import firebase_tokens
from assistant.integrations.redis import get_redis
from assistant.integrations.services import KEY_CLAIMS
from assistant.models.oauth_tokens import Access
from assistant.models.tools import Tool
from assistant.repositories import oauth
from assistant.services import updates
from assistant.services.actions import checked_arguments, count_action
from assistant.services.mcp_keys import key_may_use, key_refusal, key_signed_in
from assistant.services.registry import tools
from assistant.services.tenancy import foreign_company, user_companies
from assistant.services.tool_calls import call_tool

logger = logging.getLogger(__name__)


def writes_allowed(access: Access) -> bool:
    """Whether the connection may change things: a read-only one (MCP_READ_SCOPE) may not."""
    return MCP_SCOPE in access.scopes


def listed(access: Access | None = None) -> list[types.Tool]:
    """Every tool an AI app may call; for an API key, those its permissions allow; for a
    read-only connection, the reads."""
    return [
        mcp_tool(tool)
        for name, tool in tools().items()
        if name not in MCP_EXCLUDED | MCP_UNLISTED
        and (
            access is None
            or (key_may_use(access, name) and (tool.method == "GET" or writes_allowed(access)))
        )
    ]


def text_result(content: dict, error: bool) -> types.CallToolResult:
    """The result as structured content, and as its JSON text for apps that read only text."""
    text = json.dumps(content, ensure_ascii=False, default=str)

    return types.CallToolResult(
        content=[types.TextContent(text=text)],
        structured_content=json.loads(text),
        is_error=error,
    )


def error_result(detail: str) -> types.CallToolResult:
    return text_result({"error": detail}, True)


async def count_call(user_id: str) -> None:
    """Counts one call of the user's apps; over a limit, a 429. With Redis down, not counted."""
    redis = get_redis()
    minute = f"rate:assistant:mcp:minute:{user_id}"
    await hit_or_skip(redis, minute, "MCP_CALLS_PER_USER_MINUTE", user_id=user_id)
    day = f"rate:assistant:mcp:day:{user_id}"
    await hit_or_skip(redis, day, "MCP_CALLS_PER_USER_DAY", user_id=user_id)


async def mark_active(access: Access) -> None:
    """The connection's last use (an API key's is the api service's), and the funnel's
    mcp_active once a day for each user and app. Neither ever fails the call."""
    client = KEY_FUNNEL_CLIENT if access.key_id else funnel_client(access.client_name)

    try:
        if access.grant_id:
            async with Session.begin() as session:
                await oauth.used(session, uuid.UUID(access.grant_id), datetime.now(UTC))

        key = ACTIVE_KEY.format(user_id=access.subject, client=client)

        if await get_redis().set(key, 1, ex=DAY_SECONDS, nx=True):
            await track("mcp_active", user_id=access.subject, client=client)
    except Exception:
        logger.warning("Couldn't record an AI app's use", exc_info=True)


async def checked_write(tool: Tool, arguments: dict, user: User, token: str) -> dict:
    """A write's arguments once it may run, as in the app: nothing while paused, about something
    the user may see, with only what changes, within their hourly actions. Otherwise an
    HTTPException saying why not."""
    redis = get_redis()
    company_id = arguments.get("company_id")
    await refuse_if_paused(redis, "mcp_action", company_id, user.uid)
    arguments, _ = await checked_arguments(tool, arguments, token, user.language)
    await count_action(redis, user.uid, company_id)

    return arguments


def logged(why: str, name: str, access: Access, detail: str) -> types.CallToolResult:
    """A refused call as the app reads it, logged with ids and the tool's name only: never the
    token or the arguments. An unknown tool's name is the app's text, so only its start."""
    connection = access.key_id or access.grant_id
    logger.info(
        "An AI app's call was refused (%s): tool %s, user %s, connection %s",
        why,
        name[:MAX_LOGGED_TOOL_NAME],
        access.subject,
        connection,
    )

    return error_result(detail)


def refusal(name: str, tool: Tool | None, access: Access) -> types.CallToolResult | None:
    """Why an app may not call this tool at all (logged), or None."""
    if name in MCP_EXCLUDED:
        return logged("excluded tool", name, access, EXCLUDED_TOOL)

    if tool is None:
        return logged("unknown tool", name, access, UNKNOWN_TOOL)

    if not key_may_use(access, name):
        return logged("key permission", name, access, key_refusal(name))

    if tool.method != "GET" and not writes_allowed(access):
        return logged("read-only connection", name, access, READ_ONLY)

    return None


async def run(
    name: str, tool: Tool, arguments: dict, access: Access, user: User, token: str
) -> types.CallToolResult:
    """The checked call itself: the result as the app reads it, with absolute links."""
    if name == GET_UPDATES:
        result = await updates.for_app(arguments, access, token, user.language)

        if not result.succeeded:
            return error_result(result.content["detail"])

        return text_result(result.content, False)

    result = await call_tool(
        name,
        arguments,
        token,
        user.language,
        arguments.get("company_id"),
        str(uuid.uuid4()) if tool.method != "GET" else None,
        via=VIA_MCP,
    )

    if tool.method != "GET":
        await track("mcp_action", user_id=user.uid, tool=name, ok=result.succeeded)

    if name == UPDATE_LANGUAGE and result.succeeded:
        firebase_tokens.forget(user.uid)

    if not result.succeeded:
        return error_result(result.content["detail"])

    site = settings.site_url.rstrip("/")
    links = [site + link for link in (result.block or {}).get("links", []) if link]
    content = {**result.content, "links": links} if links else result.content

    return text_result(content, False)


async def call(name: str, arguments: dict, access: Access) -> types.CallToolResult:
    """One tool, called by an AI app as the user it acts for. A write runs at once: the app asked
    the user before calling it. Its result is the data as JSON, with links to testee's pages;
    an error is a result too, which the app explains."""
    tool = tools().get(name) if name not in MCP_UNLISTED else None
    # An API key acts as itself; an AI app as the user who connected it.
    signed_in = (
        key_signed_in(access) if access.key_id else await firebase_tokens.sign_in(access.subject)
    )

    if signed_in is None:
        return logged("account gone", name, access, ACCOUNT_GONE)

    user, token = signed_in

    try:
        # Refused calls count too, so probing for tools or slipping secrets in is limited.
        await count_call(user.uid)
    except HTTPException as error:
        return error_result(translate(str(error.detail), user.language))

    refused = refusal(name, tool, access)

    if refused:
        return refused

    # Secrets are never sent through an AI app: entered in testee itself only. Any string
    # counts, however deep in a list or an object.
    if secret_in(texts_in(arguments)) is not None:
        return logged("secret in arguments", name, access, translate(SECRET_REMOVED, user.language))

    # An API key's company: companies refuses any other one (the X-Assistant header).
    if access.key_id:
        KEY_CLAIMS.set({"company": access.company_id, "key": access.key_id})

    try:
        await mark_active(access)
        companies = (
            frozenset({access.company_id}) if access.key_id else await user_companies(user.uid)
        )

        # As in the app's panel: a company that isn't one of the user's (or the key's) isn't
        # called at all.
        if foreign_company(arguments, companies):
            detail = translate(OTHER_COMPANY, user.language)

            return logged("company not the user's", name, access, detail)

        if tool.method != "GET":
            arguments = await checked_write(tool, arguments, user, token)
    except HTTPException as error:
        return error_result(translate(str(error.detail), user.language))

    return await run(name, tool, arguments, access, user, token)
