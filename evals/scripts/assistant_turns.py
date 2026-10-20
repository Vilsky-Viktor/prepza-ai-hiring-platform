"""One assistant turn run inside the service, as a panel message would run it: with the page
context (as the service does now) or without it (as before: the page's path alone, no
get_page_guide tool and no page instructions, earlier messages without their page)."""

import asyncio
import base64
import json
import re
import time
import uuid
from contextlib import contextmanager
from types import SimpleNamespace

from common import cost
from fastapi import HTTPException

from app.config.settings import settings
from app.constants.chat import HISTORY_CHARACTERS, Role
from app.models.answers import Answer, Turn
from app.services import chat, show
from app.services.registry import tools
from app.services.tenancy import user_companies
from app.storage import actions

# What answers, for the results.
MODEL = f"{settings.assistant_model} ({settings.assistant_reasoning_effort})"

# Reading the user's companies is tried this many times, this many seconds apart: the local
# stack's services restart when their code changes.
COMPANIES_TRIES = 5
COMPANIES_WAIT_SECONDS = 3
# The context line before the page context, which named the path alone.
OLD_PAGE = "The user is on the page {page}."
PAGE_TOOL = "get_page_guide"


def without_page_instructions(system: str) -> str:
    """The instructions without their bullet about the page the user asks from."""
    old = re.sub(r"- The user asks from a page.*?\n(?=- \{scope\})", "", system, flags=re.DOTALL)

    if old == system:
        raise ValueError("The page instructions weren't found: update without_page_instructions")

    return old


@contextmanager
def before_page_context():
    """The service as it was before the page context, for this block."""
    saved = (chat.ASSISTANT_SYSTEM, chat.CURRENT_PAGE, chat.describe_page, chat.tools)
    chat.ASSISTANT_SYSTEM = without_page_instructions(chat.ASSISTANT_SYSTEM)
    chat.CURRENT_PAGE = OLD_PAGE
    chat.describe_page = lambda page: page["path"].split("?")[0]
    chat.tools = lambda: {name: tool for name, tool in tools().items() if name != PAGE_TOOL}

    try:
        yield
    finally:
        chat.ASSISTANT_SYSTEM, chat.CURRENT_PAGE, chat.describe_page, chat.tools = saved


def user_id(token: str) -> str:
    payload = token.split(".")[1]

    return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))["user_id"]


async def companies_of(uid: str) -> frozenset[str]:
    """The user's companies, read again while companies restarts."""
    for _ in range(COMPANIES_TRIES - 1):
        try:
            return await user_companies(uid)
        except HTTPException:
            await asyncio.sleep(COMPANIES_WAIT_SECONDS)

    return await user_companies(uid)


async def ask(
    token: str, owner: str, company_id: str | None, message: str, page: dict, earlier: list
) -> dict:
    """One message, on `page` (the context the panel sends), after `earlier` turns ({role,
    content, page}); the answer's text, tool calls (with why one was refused), the actions it
    prepared for the user to confirm, shown rows, the pages linked under it (by the model or by
    code), tokens, cost and seconds."""
    uid = user_id(token)
    companies = await companies_of(uid)
    picked = uuid.UUID(company_id) if company_id else None
    turn = Turn(uuid.uuid4(), uid, picked, token, "en", companies, owner)
    stored = [
        SimpleNamespace(role=Role(item["role"]), content=item["content"], page=item.get("page"))
        for item in earlier
    ]
    messages = chat.build_messages(turn, stored, message, page, HISTORY_CHARACTERS)
    answer = Answer()
    started = time.monotonic()

    try:
        await chat.converse(messages, turn, answer, lambda event: None)
        # What goes under the answer once it's written, with the link code adds when the
        # model gave none.
        await show.finish(answer, turn, lambda event: None)
        error = None
    except Exception as failure:  # noqa: BLE001 - a failed turn is a result too
        error = type(failure).__name__

    seconds = round(time.monotonic() - started, 2)
    usage = {"input_tokens": answer.input_tokens, "output_tokens": answer.output_tokens}
    # A prepared action is kept in Redis only, until the user confirms or cancels its card.
    prepared = [await actions.peek(action_id) for action_id in answer.pending]

    return {
        "text": answer.content,
        "tools": [
            {
                "name": item.tool,
                "arguments": item.arguments,
                "refused": None if item.succeeded else item.content.get("detail"),
            }
            for item in answer.results
        ],
        "actions": [
            {"name": item["tool"], "arguments": item["arguments"]} for item in prepared if item
        ],
        "shown": [
            {
                "kind": block["kind"],
                "items": block.get("items", []),
                "links": block.get("links", []),
            }
            for block in answer.shown_blocks
        ],
        "linked": [block["page"] for block in answer.blocks if block["kind"] == "link"],
        "error": error,
        "tokens": answer.tokens,
        "cost": cost(settings.assistant_model, usage),
        "seconds": seconds,
    }


def readable(result: dict) -> str:
    """An answer as a judge reads it."""
    tools_text = "\n".join(
        f"- {item['name']}({json.dumps(item['arguments'], ensure_ascii=False)})"
        for item in result["tools"]
    )
    shown = json.dumps(result["shown"], ensure_ascii=False) if result["shown"] else "none"
    failed = f"\n(The turn failed: {result['error']})" if result["error"] else ""

    return (
        f"Text:\n{result['text'] or '(none)'}{failed}\n"
        f"Tools:\n{tools_text or '(none)'}\nRows shown: {shown}"
    )
