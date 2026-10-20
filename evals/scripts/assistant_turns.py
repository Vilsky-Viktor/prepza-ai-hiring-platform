"""One assistant turn run inside the service, as a panel message would run it: with the page
context (as the service does now) or without it (as before: the page's path alone, no
get_page_guide tool and no page instructions, earlier messages without their page)."""

import base64
import json
import re
import uuid
from contextlib import contextmanager
from types import SimpleNamespace

from common import cost

from app.config.settings import settings
from app.constants.chat import HISTORY_CHARACTERS, Role
from app.models.answers import Answer, Turn
from app.services import chat
from app.services.registry import tools
from app.services.tenancy import user_companies

# What answers, for the results.
MODEL = f"{settings.assistant_model} ({settings.assistant_reasoning_effort})"

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


async def ask(
    token: str, owner: str, company_id: str | None, message: str, page: dict, earlier: list
) -> dict:
    """One message, on `page` (the context the panel sends), after `earlier` turns ({role,
    content, page}); the answer's text, tool calls, shown rows, tokens and cost."""
    uid = user_id(token)
    companies = await user_companies(uid)
    picked = uuid.UUID(company_id) if company_id else None
    turn = Turn(uuid.uuid4(), uid, picked, token, "en", companies, owner)
    stored = [
        SimpleNamespace(role=Role(item["role"]), content=item["content"], page=item.get("page"))
        for item in earlier
    ]
    messages = chat.build_messages(turn, stored, message, page, HISTORY_CHARACTERS)
    answer = Answer()

    try:
        await chat.converse(messages, turn, answer, lambda event: None)
        error = None
    except Exception as failure:  # noqa: BLE001 - a failed turn is a result too
        error = type(failure).__name__

    usage = {"input_tokens": answer.input_tokens, "output_tokens": answer.output_tokens}

    return {
        "text": answer.content,
        "tools": [{"name": item.tool, "arguments": item.arguments} for item in answer.results],
        "shown": [
            {
                "kind": block["kind"],
                "items": block.get("items", []),
                "links": block.get("links", []),
            }
            for block in answer.shown_blocks
        ],
        "error": error,
        "tokens": answer.tokens,
        "cost": cost(settings.assistant_model, usage),
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
