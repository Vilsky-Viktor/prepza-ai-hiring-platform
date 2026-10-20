import asyncio
import json
from collections.abc import Callable
from datetime import UTC, datetime

from langchain_core.messages import (
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from prepza_common import ai_usage
from prepza_common.ai_constants import Outcome
from prepza_common.constants import LANGUAGES
from prepza_common.i18n import translate
from prepza_common.llm import estimated_input, estimated_tokens
from prepza_common.scope import SCOPE_RULE
from prepza_common.tracing import new_trace_id, traced

from app.config.settings import settings
from app.constants.ai_usage import MESSAGE_ACTION
from app.constants.chat import COMPANY_NOT_FOUND, MAX_TOOL_STEPS, ToolState
from app.constants.client_tools import SIGN_OUT, SIGN_OUT_DEFINITION, SIGN_OUT_FOR_MODEL
from app.constants.show import SHOW, SHOW_DEFINITION
from app.constants.tool_calls import INVALID_ARGUMENTS
from app.constants.tool_labels import ACTION_LABEL, TOOL_LABELS, UNKNOWN_TOOL_LABEL
from app.constants.updates import GET_UPDATES
from app.helpers.history import history
from app.helpers.page_context import describe_page
from app.integrations import llm
from app.models.answers import Answer, Turn
from app.models.tools import ToolResult
from app.prompts.assistant import (
    ASSISTANT_SYSTEM,
    COMPANY_CONTEXT,
    CURRENT_PAGE,
    NO_COMPANY_CONTEXT,
    NO_USER_NAME,
    UNKNOWN_PAGE,
    USER_CONTEXT,
)
from app.prompts.parents import PARENTS_RULE
from app.services.actions import prepare
from app.services.registry import tools
from app.services.show import show
from app.services.tenancy import foreign_company
from app.services.tool_calls import call_tools
from app.services.updates import in_panel

# Each event the turn sends the panel goes through one of these.
Emit = Callable[[dict], None]


class SessionExpired(Exception):
    """A service refused the user's token mid-turn."""


def build_messages(
    turn: Turn, earlier: list, message: str, page: dict | None, room: int
) -> list[BaseMessage]:
    """The instructions with the page the user asks on (`page`, as stored with the message), the
    conversation's latest messages within `room` characters (see helpers/history.py) and the
    new message."""
    company = (
        COMPANY_CONTEXT.format(company_id=turn.company_id)
        if turn.company_id
        else NO_COMPANY_CONTEXT
    )
    system = ASSISTANT_SYSTEM.format(
        language=LANGUAGES[turn.language],
        today=datetime.now(UTC).date().isoformat(),
        company=company,
        page=CURRENT_PAGE.format(page=describe_page(page)) if page else UNKNOWN_PAGE,
        scope=SCOPE_RULE,
        parents=PARENTS_RULE,
        user=USER_CONTEXT.format(name=json.dumps(turn.user_name))
        if turn.user_name
        else NO_USER_NAME,
    )

    return [
        SystemMessage(content=system),
        *history(earlier, room, with_pages=True),
        HumanMessage(content=message),
    ]


async def converse(messages: list[BaseMessage], turn: Turn, answer: Answer, emit: Emit) -> None:
    """Asks the model, runs the tools it calls and asks again with their results, streaming its
    text, until it answers without tools. After MAX_TOOL_STEPS steps with tools, it must answer
    with what it has."""
    definitions = [tool.definition for tool in tools().values()]
    definitions += [SIGN_OUT_DEFINITION, SHOW_DEFINITION]
    model = llm.get_chat_model()

    for step in range(MAX_TOOL_STEPS + 1):
        last = step == MAX_TOOL_STEPS
        bound = model.bind_tools(definitions, tool_choice="none" if last else "auto")
        reply = await ask(bound, messages, turn, answer, emit)
        calls = [*reply.tool_calls, *reply.invalid_tool_calls]

        if last or not calls:
            return

        messages.append(reply)
        messages += await run_tools(calls, turn, answer, emit)


async def ask(
    model, messages: list[BaseMessage], turn: Turn, answer: Answer, emit: Emit
) -> AIMessageChunk:
    """One model call: its text streams to the panel as it comes; its tokens are counted and
    recorded, and estimated when the call is cut short (cancelled, timed out, failed), which
    reports none, though the model read the messages and wrote what came."""
    reply = AIMessageChunk(content="")
    outcome = Outcome.OK
    # Every model call of the answer reports to its one Langfuse trace, kept with the answer.
    answer.trace_id = answer.trace_id or new_trace_id()

    try:
        async for chunk in model.astream(messages, traced(answer.trace_id)):
            reply += chunk

            if chunk.text:
                answer.parts.append(chunk.text)
                emit({"delta": chunk.text})
    except asyncio.CancelledError:
        outcome = Outcome.CUT

        raise
    except Exception as error:
        outcome = Outcome.FAILED
        await ai_usage.provider_refused(error, MESSAGE_ACTION, turn.company_id, turn.user_id)

        raise
    finally:
        usage = reply.usage_metadata or {
            "input_tokens": estimated_input(messages),
            "output_tokens": estimated_tokens(str(reply.content) + str(reply.tool_call_chunks)),
        }
        answer.input_tokens += usage["input_tokens"]
        answer.output_tokens += usage["output_tokens"]
        await ai_usage.record(
            MESSAGE_ACTION,
            settings.assistant_model,
            usage,
            company_id=turn.company_id,
            user_id=turn.user_id,
            subject_id=turn.conversation_id,
            outcome=outcome,
        )

    return reply


def tool_event(name: str, state: ToolState, language: str) -> dict:
    tool = tools().get(name)
    fallback = ACTION_LABEL if tool is not None and tool.confirm else UNKNOWN_TOOL_LABEL
    label = translate(TOOL_LABELS.get(name, fallback), language)

    return {"tool": {"name": name, "state": state, "label": label}}


async def step_results(
    calls: list[tuple[str, dict]], turn: Turn, shown: set | None = None
) -> list[ToolResult]:
    """One step's results, in order: a call naming a company that isn't the user's is refused
    before anything runs; an action is prepared for the user to confirm; reads are called."""
    results: list[ToolResult | None] = [None] * len(calls)
    reads = []

    for index, (name, arguments) in enumerate(calls):
        tool = tools().get(name)

        if name == SHOW:
            # Rows or a link under the answer, which the model chose (one of each at most).
            content, block = await show(arguments, turn, shown if shown is not None else set())
            results[index] = ToolResult(name, arguments, 200, content, block, 0)
        elif name == SIGN_OUT:
            # Signing out happens in the browser: the panel is told to (run_tools).
            content = {"detail": SIGN_OUT_FOR_MODEL}
            results[index] = ToolResult(name, {}, 200, content, None, 0)
        elif foreign_company(arguments, turn.companies):
            content = {"error": 404, "detail": translate(COMPANY_NOT_FOUND, turn.language)}
            results[index] = ToolResult(name, arguments, None, content, None, 0)
        elif tool is not None and tool.confirm:
            results[index] = await prepare(tool, arguments, turn)
        elif name == GET_UPDATES:
            results[index] = await in_panel(arguments, turn)
        else:
            reads.append(index)

    called = await call_tools(
        [calls[index] for index in reads],
        turn.token,
        turn.language,
        str(turn.company_id) if turn.company_id else None,
    )

    for index, result in zip(reads, called, strict=True):
        results[index] = result

    return results


async def run_tools(calls: list[dict], turn: Turn, answer: Answer, emit: Emit) -> list[ToolMessage]:
    """One step's tool calls, at once; their results for the model, and their progress and
    blocks for the panel. A call whose arguments aren't JSON gets an error the model can fix."""
    for call in calls:
        emit(tool_event(call["name"], ToolState.RUNNING, turn.language))

    valid = [call for call in calls if call.get("type") == "tool_call"]
    results = await step_results(
        [(call["name"], call["args"]) for call in valid], turn, answer.shown
    )
    replies = []

    for call, result in zip(valid, results, strict=True):
        if result.tool == SIGN_OUT:
            emit({"sign_out": True})

        # A card to confirm isn't kept with the answer: only in Redis, until it's handled.
        pending = result.action_id is not None

        if pending:
            answer.pending.append(result.action_id)
        state = ToolState.DONE if result.succeeded or pending else ToolState.FAILED
        emit(tool_event(call["name"], state, turn.language))

        # A prepared action's card and arguments aren't kept with the answer: only in Redis,
        # until the user confirms or cancels it.
        if not pending:
            answer.results.append(result)

        # What the model shows goes under the answer once it's written (show.finish); an
        # action's card, at once.
        if result.block is not None and "ref" in result.block:
            answer.shown_blocks.append(result.block)
        elif result.block is not None:
            emit({"block": result.block})

        content = json.dumps(result.content, ensure_ascii=False)
        replies.append(ToolMessage(content=content, tool_call_id=call["id"]))

    for call in calls:
        if call.get("type") != "tool_call":
            emit(tool_event(call.get("name") or "", ToolState.FAILED, turn.language))
            error = {"error": 422, "detail": translate(INVALID_ARGUMENTS, turn.language)}
            replies.append(ToolMessage(content=json.dumps(error), tool_call_id=call["id"]))

    if any(result.status_code == 401 for result in results):
        raise SessionExpired

    return replies
