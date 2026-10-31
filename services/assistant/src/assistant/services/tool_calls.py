import time

import httpx
from testee_common.config.constants import VIA_ASSISTANT
from testee_common.http.capped import gather_capped
from testee_common.i18n.i18n import translate

from assistant.config import settings
from assistant.constants.tool_calls import (
    ASK_TO_NARROW,
    INVALID_ARGUMENTS,
    MAX_PARALLEL_TOOL_CALLS,
    MORE_ITEMS,
    NARROW_WITH,
    NEXT_PAGE,
    NOT_FILTERS,
    SERVICE_UNAVAILABLE,
    UNKNOWN_TOOL,
)
from assistant.helpers.arguments import fill_path, problems
from assistant.helpers.blocks import render_block
from assistant.helpers.links import with_links
from assistant.helpers.trimming import trim
from assistant.integrations import services
from assistant.models.tools import Tool, ToolResult
from assistant.services.registry import tools


async def call_tools(
    calls: list[tuple[str, dict]], token: str, language: str, company_id: str | None
) -> list[ToolResult]:
    """One step's tool calls, at most MAX_PARALLEL_TOOL_CALLS at a time, in the given order."""
    return await gather_capped(
        MAX_PARALLEL_TOOL_CALLS,
        (call_tool(name, arguments, token, language, company_id) for name, arguments in calls),
    )


async def call_tool(
    name: str,
    arguments: dict,
    token: str,
    language: str,
    company_id: str | None,
    idempotency_key: str | None = None,
    via: str = VIA_ASSISTANT,
    referral: str | None = None,
) -> ToolResult:
    """Calls one tool as the user (a write only once they confirmed it, with its id as the
    idempotency key), through the assistant or an AI app (`via`). Errors are results too, which the model explains: an unknown
    tool, refused arguments, the service's own error (its detail is in the user's language) or
    no answer."""
    started = time.monotonic()

    def result(status: int | None, content: dict, block: dict | None = None) -> ToolResult:
        duration = round((time.monotonic() - started) * 1000)

        return ToolResult(name, arguments, status, content, block, duration)

    tool = tools().get(name)

    if tool is None:
        return result(None, {"error": 404, "detail": translate(UNKNOWN_TOOL, language)})

    found = problems(arguments, tool.parameters)

    if found:
        detail = f"{translate(INVALID_ARGUMENTS, language)}: {'; '.join(found)}"

        return result(None, {"error": 422, "detail": detail})

    given = {key: value for key, value in arguments.items() if value is not None}
    wanted = min(given.get("limit", tool.max_items), tool.max_items)
    query = {param: given[param] for param in tool.query_params if param in given}

    # One more than wanted, to tell whether there are more.
    if "limit" in tool.query_params:
        query["limit"] = wanted + 1

    path = fill_path(tool.path, {param: given[param] for param in tool.path_params})
    body = {field: given[field] for field in tool.body_params if field in given}

    try:
        if tool.method == "GET":
            response = await services.get(tool.service, path, query, token, language, via=via)
        else:
            response = await services.send(
                tool.service,
                tool.method,
                path,
                query,
                body,
                token,
                language,
                idempotency_key,
                via=via,
                referral=referral,
            )
    except httpx.TimeoutException:
        return result(None, {"error": 504, "detail": translate(SERVICE_UNAVAILABLE, language)})
    except httpx.HTTPError:
        return result(None, {"error": 503, "detail": translate(SERVICE_UNAVAILABLE, language)})

    if not response.is_success:
        return result(response.status_code, error_content(response, language))

    content, data = read(tool, response, wanted, given.get("offset", 0))
    context = {"company_id": company_id, **given}

    return result(
        response.status_code, content, render_block(tool.render, tool.link, data, context)
    )


def read(tool: Tool, response: httpx.Response, wanted: int, offset: int = 0) -> tuple[dict, object]:
    """What the model reads of a successful answer, and the trimmed data alone."""
    is_json = response.headers.get("content-type", "").startswith("application/json")
    # A write may answer with no body at all (204).
    data = response.json() if is_json and response.content else response.text or None
    more = isinstance(data, list) and len(data) > wanted

    if more:
        data = data[:wanted]

    data = trim(with_links(data, settings.site_url), tool.fields, tool.max_items, tool.max_length)
    content = {"data": data, "source": tool.name}

    if more:
        content |= {"shown": len(data), "more": True, "narrow": narrowing(tool, offset + len(data))}

    return content, data


def narrowing(tool: Tool, next_offset: int) -> str:
    """How the model sees the rest of a list cut short: the tool's own filters, or asking the
    user, and the next page when the tool pages."""
    filters = [param for param in tool.query_params if param not in NOT_FILTERS]
    hint = [
        MORE_ITEMS,
        NARROW_WITH.format(filters=", ".join(filters)) if filters else ASK_TO_NARROW,
    ]

    if "offset" in tool.query_params:
        hint.append(NEXT_PAGE.format(offset=next_offset))

    return " ".join(hint)


def error_content(response: httpx.Response, language: str) -> dict:
    """The service's error as the model reads it: its status and its message, already in the
    user's language (the services translate by Accept-Language)."""
    try:
        body = response.json()
    except ValueError:
        body = None

    detail = body.get("detail") if isinstance(body, dict) else None

    if not isinstance(detail, str):
        detail = (
            translate(INVALID_ARGUMENTS, language)
            if response.status_code == 422
            else response.reason_phrase
        )

    return {"error": response.status_code, "detail": detail}
