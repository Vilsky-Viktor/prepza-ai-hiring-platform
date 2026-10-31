import time
from datetime import UTC, datetime, timedelta

from testee_common.config.constants import VIA_ASSISTANT, VIA_MCP
from testee_common.i18n.i18n import translate

from assistant.config import settings
from assistant.constants.tool_calls import INVALID_ARGUMENTS
from assistant.constants.updates import (
    CREDITS_TOOL,
    FIRST_CHECK_DAYS,
    GET_UPDATES,
    GET_UPDATES_DEFINITION,
    INVALID_SINCE,
    SETTLE_SECONDS,
)
from assistant.core.db import Session
from assistant.helpers.arguments import problems
from assistant.helpers.updates import parsed_since
from assistant.models.answers import Turn
from assistant.models.oauth_tokens import Access
from assistant.models.tools import ToolResult
from assistant.repositories import update_checks
from assistant.services.mcp_keys import key_may_use
from assistant.services.update_sources import Refused, read


def given_since(arguments: dict, language: str) -> datetime | None:
    """The `since` the call asks for, once its arguments are right; None when it asks for none."""
    found = problems(arguments, GET_UPDATES_DEFINITION["function"]["parameters"])

    if found:
        raise Refused(422, f"{translate(INVALID_ARGUMENTS, language)}: {'; '.join(found)}")

    if not arguments.get("since"):
        return None

    since = parsed_since(arguments["since"])

    if since is None:
        raise Refused(422, translate(INVALID_SINCE, language))

    return since


async def for_app(arguments: dict, access: Access, token: str, language: str) -> ToolResult:
    """An AI app's (or API key's) call: since its connection's last check, the first time the
    last FIRST_CHECK_DAYS days, or the `since` it asks for, which doesn't count as a check; up
    to where the next check starts, so nothing is told twice or missed. Only companies
    that allow AI apps; low credits only for a key that may read credits; links on the site."""
    started = time.monotonic()
    # A step saved in a transaction still open is stamped before it can be read: the check
    # ends SETTLE_SECONDS ago, so the next one, starting there, still finds it.
    now = datetime.now(UTC) - timedelta(seconds=SETTLE_SECONDS)
    connection = access.key_id or access.grant_id

    try:
        since = given_since(arguments, language)
        asked = since is not None

        if since is None:
            async with Session() as session:
                last = await update_checks.last(session, connection)

            since = last or now - timedelta(FIRST_CHECK_DAYS)

        period = (since, now)
        sees_credits = key_may_use(access, CREDITS_TOOL)
        content = await read(
            arguments, token, language, period, VIA_MCP, settings.site_url.rstrip("/"), sees_credits
        )
    except Refused as refused:
        return result(arguments, started, refused.status, {"detail": refused.detail})

    if not asked:
        async with Session.begin() as session:
            await update_checks.save(session, connection, now)

    return result(arguments, started, 200, content)


async def in_panel(arguments: dict, turn: Turn) -> ToolResult:
    """The panel's call: the panel is no connection, so the last FIRST_CHECK_DAYS days, or the
    `since` the model asks for; every company of the user's; links as the app's paths."""
    started = time.monotonic()

    try:
        since = given_since(arguments, turn.language)
        now = datetime.now(UTC)
        period = (since or now - timedelta(FIRST_CHECK_DAYS), now)
        content = await read(
            arguments, turn.token, turn.language, period, VIA_ASSISTANT, "", sees_credits=True
        )
    except Refused as refused:
        return result(arguments, started, refused.status, {"detail": refused.detail})

    return result(arguments, started, 200, content)


def result(arguments: dict, started: float, status: int, content: dict) -> ToolResult:
    duration = round((time.monotonic() - started) * 1000)

    # As other tools' results: the data and where it came from, or the error and why.
    if status == 200:
        content = {"data": content, "source": GET_UPDATES}
    else:
        content = {"error": status, **content}

    return ToolResult(GET_UPDATES, arguments, status, content, None, duration)
