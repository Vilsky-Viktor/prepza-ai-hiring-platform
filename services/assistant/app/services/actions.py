import uuid
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from prepza_common.i18n import translate
from prepza_common.pause import refuse_if_paused
from prepza_common.rate_limit import hit
from prepza_common.user import User

from app.constants.actions_flow import (
    ACTION_GONE,
    CANCELLED,
    DONE,
    FAILED,
    NOTHING_TO_CHANGE,
    PENDING,
    PENDING_FOR_MODEL,
    SUBJECT_NOT_FOUND,
    UNKNOWN_EMAIL,
)
from app.constants.chat import SESSION_EXPIRED
from app.helpers.arguments import fill_path, problems
from app.helpers.given_emails import unknown_emails
from app.helpers.untrusted_text import without_instructions
from app.integrations import services
from app.integrations.redis import get_redis
from app.models.answers import Turn
from app.models.tools import Tool, ToolResult
from app.services import limits
from app.services.conversations import open_conversation
from app.services.registry import tools
from app.services.tenancy import require_company, user_companies
from app.services.tool_calls import call_tool
from app.storage import actions


def card(action_id: UUID, tool: Tool, arguments: dict, state: str, **more) -> dict:
    """The confirmation card's block: the action, what it's about (`subject`), the arguments it
    shows (exactly what runs), whether it can't be undone, and its state."""
    shown = {name: arguments[name] for name in tool.preview if arguments.get(name) is not None}

    return {
        "kind": "confirm",
        "items": [],
        "links": more.pop("links", []),
        "action_id": str(action_id),
        "tool": tool.name,
        "preview": shown,
        "company_id": arguments.get("company_id"),
        "destructive": tool.destructive,
        "state": state,
        **more,
    }


async def subject_of(tool: Tool, arguments: dict, token: str, language: str) -> dict | None:
    """What the action is about, as the user may see it now (a company, an interview), read
    with their token; raises LookupError when it's not theirs or is gone."""
    entry = tool.subject

    if entry is None:
        return None

    path = fill_path(entry["path"], arguments)
    query = {name: arguments[name] for name in entry.get("query", []) if name in arguments}

    try:
        response = await services.get(entry["service"], path, query, token, language)
    except httpx.HTTPError:
        return None

    if not response.is_success:
        raise LookupError

    data = response.json()

    if isinstance(data, list):
        wanted = str(arguments[entry["match"]])
        data = next((item for item in data if str(item.get("id")) == wanted), None)

        if data is None:
            raise LookupError

    return data if isinstance(data, dict) else None


def unchanged(tool: Tool, arguments: dict, current: dict | None) -> dict:
    """A partial update (PATCH) without the values that are already so, which the model may
    have copied from what it read: the card shows, and the action sends, only what changes."""
    if tool.method != "PATCH" or current is None:
        return arguments

    return {
        name: value
        for name, value in arguments.items()
        if name not in tool.body_params or current.get(name) != value
    }


async def credits_lost(tool: Tool, company_id: str | None, turn: Turn) -> dict | None:
    """The company's credits an action would lose (deleting it), as the user may see them:
    {available, candidates}; None when it has none or they can't be read."""
    if company_id is None:
        return None

    path = f"/companies/{company_id}/credits"

    try:
        response = await services.get("companies", path, {}, turn.token, turn.language)
    except httpx.HTTPError:
        return None

    found = response.json() if response.is_success else {}

    if found.get("available", 0) <= 0:
        return None

    return {"available": found["available"], "candidates": found.get("candidates", 0)}


async def checked_arguments(
    tool: Tool, arguments: dict, token: str, language: str
) -> tuple[dict, dict | None]:
    """A write's arguments with only what changes, and what it's about as it is now, read with
    the user's token: a 404 when it isn't theirs to see, a 422 when nothing would change. The
    same checks for the panel's actions and AI apps' writes."""
    try:
        current = await subject_of(tool, arguments, token, language)
    except LookupError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, SUBJECT_NOT_FOUND)

    arguments = unchanged(tool, arguments, current)

    if tool.body_params and not any(name in arguments for name in tool.body_params):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, NOTHING_TO_CHANGE)

    return arguments, current


async def count_action(redis, user_id: str, company_id: object | None = None) -> None:
    """Counts one write of the user's, in the panel or an AI app; over the hourly limit, a 429."""
    key = f"rate:assistant:actions:{user_id}"
    await hit(redis, key, "ACTIONS_PER_USER_HOUR", company_id=company_id, user_id=user_id)


def cleaned(tool: Tool, arguments: dict) -> dict:
    """An action's texts (its body's fields) without what data may hide in them to steer the
    assistant, which may have copied them from an ATS job or a pasted description: hidden
    content and parts addressed to an AI. The user's visible words stay."""
    return {
        name: without_instructions(value)
        if name in tool.body_params and isinstance(value, str)
        else value
        for name, value in arguments.items()
    }


async def prepare(tool: Tool, arguments: dict, turn: Turn, seen: str | None = None) -> ToolResult:
    """What the model asked for, its texts cleaned, kept (in Redis, for a short while) for the
    user to confirm: bound to them, the conversation and the company. Nothing runs yet; what
    it's about is read with the user's token to name it on the card, and must be theirs to
    see. With `seen` (what the user wrote and the tools returned), an address in its texts
    must be one of those: the model never invents one."""
    arguments = cleaned(tool, arguments)
    found = problems(arguments, tool.parameters)

    if seen is not None:
        found += [
            UNKNOWN_EMAIL.format(address=address)
            for address in unknown_emails(arguments, tool.body_params, seen)
        ]

    if found:
        content = {"error": 422, "detail": "; ".join(found)}

        return ToolResult(tool.name, arguments, None, content, None, 0)

    try:
        arguments, current = await checked_arguments(tool, arguments, turn.token, turn.language)
    except HTTPException as error:
        content = {"error": error.status_code, "detail": translate(error.detail, turn.language)}

        return ToolResult(tool.name, arguments, None, content, None, 0)

    subject = current.get(tool.subject["field"]) if current else None

    action_id = uuid.uuid4()
    company_id = arguments.get("company_id")
    lost = await credits_lost(tool, company_id, turn) if tool.credits else None
    block = card(action_id, tool, arguments, PENDING, subject=subject, credits=lost)
    pending = {
        "user_id": turn.user_id,
        "conversation_id": str(turn.conversation_id),
        # The company it changes (checked again on confirm), and the panel's company, for the
        # link its result opens.
        "company_id": company_id,
        "context_company_id": company_id or (str(turn.company_id) if turn.company_id else None),
        "tool": tool.name,
        "arguments": arguments,
        "card": block,
    }
    await actions.save(action_id, pending)
    content = {"pending_confirmation": True, "detail": PENDING_FOR_MODEL}

    return ToolResult(tool.name, arguments, None, content, block, 0, action_id)


async def owned_action(
    conversation_id: UUID, action_id: UUID, user: User, token: str, language: str
) -> dict:
    """The pending action, when it's this user's, in this conversation, about a company that's
    still theirs (checked with their current token); a 404 otherwise, and a 409 once it's gone
    (handled, or expired)."""
    await open_conversation(conversation_id, user.uid, token, language)
    pending = await actions.peek(action_id)

    # Handled already, or expired.
    if pending is None:
        raise HTTPException(status.HTTP_409_CONFLICT, ACTION_GONE)

    if pending["user_id"] != user.uid or pending["conversation_id"] != str(conversation_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, ACTION_GONE)

    require_company(pending["company_id"], await user_companies(user.uid))

    return pending


async def claim(action_id: UUID) -> dict:
    """Takes the action for this request alone: a second confirm (or a cancel) finds it gone."""
    pending = await actions.claim(action_id)

    if pending is None:
        raise HTTPException(status.HTTP_409_CONFLICT, ACTION_GONE)

    return pending


async def cancel(conversation_id: UUID, action_id: UUID, user: User, token, language) -> dict:
    """Drops the action; the card shows it cancelled."""
    await owned_action(conversation_id, action_id, user, token, language)
    await claim(action_id)

    return {"action_id": str(action_id), "state": CANCELLED}


async def run(
    conversation_id: UUID,
    action_id: UUID,
    user: User,
    token: str,
    language: str,
    referral: str | None = None,
) -> tuple[Tool, dict, ToolResult, dict]:
    """Runs the action once, as the user, with exactly the arguments the card showed: the tool,
    the user's companies, its result and the card's new state. `referral`, the referral cookie of
    the user's browser, goes with it to companies."""
    redis = get_redis()
    await refuse_if_paused(redis, "assistant_action", user_id=user.uid)
    pending = await owned_action(conversation_id, action_id, user, token, language)
    company_id = UUID(pending["company_id"]) if pending["company_id"] else None
    await count_action(redis, user.uid, company_id)
    await limits.check(redis, user.uid, company_id)
    pending = await claim(action_id)
    tool = tools()[pending["tool"]]
    arguments = pending["arguments"]
    result = await call_tool(
        tool.name,
        arguments,
        token,
        language,
        pending["context_company_id"],
        str(action_id),
        referral=referral,
    )

    # The service refused the token: nothing ran, so it can be confirmed again once refreshed.
    if result.status_code == status.HTTP_401_UNAUTHORIZED:
        await actions.put_back(action_id, pending)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, SESSION_EXPIRED)

    done = result.succeeded
    data = result.content.get("data") if done else None
    label = data.get(tool.result_label) if tool.result_label and isinstance(data, dict) else None
    block = {
        **pending["card"],
        "state": DONE if done else FAILED,
        "links": result.block["links"] if done and result.block else [],
        "result_label": label,
        "detail": None if done else result.content.get("detail"),
    }

    return tool, pending, result, block
