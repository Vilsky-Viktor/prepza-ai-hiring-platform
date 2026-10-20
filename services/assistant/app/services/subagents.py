"""The assistant split by domain (ASSISTANT_MODE=subagents, constants/subagents.py): which tools
each agent is offered, the main agent's delegate tools and rule, and what a domain agent reads
and hands back. chat.converse runs both agents' loops; chat.delegate runs a domain's."""

import json
import time

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from prepza_common.i18n import translate
from prepza_common.tracing import child_span

from app.config.settings import settings
from app.constants.chat import COMPANY_NOT_FOUND
from app.constants.client_tools import SIGN_OUT_DEFINITION
from app.constants.show import SHOW_DEFINITION
from app.constants.subagents import (
    BRIEF_IDS,
    DELEGATE_DESCRIPTIONS,
    DELEGATE_PARAMETERS,
    DELEGATE_PREFIX,
    DOMAINS,
    MAIN_TOOLS,
    AssistantMode,
)
from app.constants.tool_calls import INVALID_ARGUMENTS
from app.models.answers import Answer, Turn
from app.models.tools import ToolResult
from app.prompts.parents import PARENTS_RULE
from app.prompts.subagents import (
    BRIEF,
    CONTEXT_HEADING,
    DELEGATION_RULE,
    DOMAIN_SYSTEM,
    NO_IDS,
    ROLES,
)
from app.services.tenancy import foreign_company


def split() -> bool:
    return settings.assistant_mode == AssistantMode.SUBAGENTS


def tool_names(domain: str | None, every: list[str]) -> list[str]:
    """The registry's tools an agent is offered, of `every` one: the main agent's (all of them
    in single mode), or a domain's own and the finders it shares."""
    if domain is not None:
        wanted = {*DOMAINS[domain]["tools"], *DOMAINS[domain]["shared"]}
    elif split():
        wanted = set(MAIN_TOOLS)
    else:
        return every

    return [name for name in every if name in wanted]


def delegate_definition(domain: str) -> dict:
    return {
        "type": "function",
        "function": {
            "name": f"{DELEGATE_PREFIX}{domain}",
            "description": DELEGATE_DESCRIPTIONS[domain],
            "parameters": DELEGATE_PARAMETERS,
        },
    }


def extra_definitions(domain: str | None) -> list[dict]:
    """The tools beside the registry's: a domain's agent shows links; the main agent also signs
    out and, split, has a delegate per domain."""
    if domain is not None:
        return [SHOW_DEFINITION]

    delegates = [delegate_definition(name) for name in DOMAINS] if split() else []

    return [SIGN_OUT_DEFINITION, SHOW_DEFINITION, *delegates]


def domain_of(name: str) -> str | None:
    """The domain a delegate tool hands work to; None for any other tool."""
    domain = name.removeprefix(DELEGATE_PREFIX)

    return domain if name.startswith(DELEGATE_PREFIX) and domain in DOMAINS else None


def main_system(system: str) -> str:
    """The main agent's instructions with the delegation rule, before the turn's context."""
    rules, context = system.split(CONTEXT_HEADING, 1)

    return f"{rules}{DELEGATION_RULE}{CONTEXT_HEADING}{context}"


def brief_messages(domain: str, arguments: dict, messages: list[BaseMessage]) -> list:
    """What a domain's agent reads: its instructions with the main agent's context (the user,
    the date, the company picked, the page), the conversation up to the user's new message, and
    the brief with the ids it passed, as data."""
    context = messages[0].content.split(CONTEXT_HEADING, 1)[1]
    system = (
        DOMAIN_SYSTEM.format(role=ROLES[domain], parents=PARENTS_RULE) + CONTEXT_HEADING + context
    )
    last = max(i for i, message in enumerate(messages) if isinstance(message, HumanMessage))
    ids = {key: arguments[key] for key in BRIEF_IDS if arguments.get(key)}
    brief = BRIEF.format(task=arguments.get("task") or "", ids=json.dumps(ids) if ids else NO_IDS)

    return [SystemMessage(content=system), *messages[1 : last + 1], HumanMessage(content=brief)]


def child_answer(answer: Answer, span_id: str | None) -> Answer:
    """A domain agent's answer: its own text and prepared actions; the calls it makes and what
    it shows go to the turn's answer (one list and one link an answer, whoever shows them), and
    its model calls report under its span of the turn's trace."""
    return Answer(
        blocks=answer.blocks,
        results=answer.results,
        shown=answer.shown,
        shown_blocks=answer.shown_blocks,
        given=answer.given,
        trace_id=answer.trace_id,
        span_id=span_id,
    )


def merge(answer: Answer, child: Answer) -> dict:
    """Adds a domain agent's tokens and prepared actions to the turn's answer; what the main
    agent reads back: the agent's reply and how many cards it put in front of the user."""
    answer.input_tokens += child.input_tokens
    answer.output_tokens += child.output_tokens
    answer.pending += child.pending

    return {"reply": child.content, "cards_shown": len(child.pending)}


def cards_only(replies: list[ToolMessage]) -> bool:
    """Whether every call of a domain agent's step prepared a card: its part is done, as a card
    says it all, so it isn't asked again. The main agent always is (a step of delegates is never
    cards only), as the request may have more parts to hand on."""
    contents = [json.loads(reply.content) for reply in replies]

    return bool(contents) and all(content.get("pending_confirmation") for content in contents)


def quiet(emit):
    """The panel's events without a domain agent's text, which only the main agent reads."""

    def send(event: dict) -> None:
        if "delta" not in event:
            emit(event)

    return send


async def delegate(
    call: dict, messages: list, turn: Turn, answer: Answer, emit, run
) -> list[ToolMessage]:
    """A domain agent does its part of the request, from the main agent's brief, in its own
    loop (`run`: chat.converse) under a span of the turn's trace; its cards and links reach the
    panel as the main agent's would, and its reply comes back as the call's result. A brief
    naming a company that isn't the user's is refused before anything runs."""
    domain, arguments = domain_of(call["name"]), call.get("args") or {}
    started = time.monotonic()

    if call.get("type") != "tool_call":
        content = {"error": 422, "detail": translate(INVALID_ARGUMENTS, turn.language)}
    elif foreign_company(arguments, turn.companies):
        content = {"error": 404, "detail": translate(COMPANY_NOT_FOUND, turn.language)}
    else:
        with child_span(answer.trace_id, call["name"]) as span:
            child = child_answer(answer, span)
            await run(brief_messages(domain, arguments, messages), turn, child, quiet(emit), domain)

        content = merge(answer, child)

    # Which domain it went to, never the brief: an answer keeps only its calls' names.
    duration = round((time.monotonic() - started) * 1000)
    status = None if "error" in content else 200
    answer.results.append(ToolResult(call["name"], {}, status, content, None, duration))

    return [ToolMessage(content=json.dumps(content, ensure_ascii=False), tool_call_id=call["id"])]
