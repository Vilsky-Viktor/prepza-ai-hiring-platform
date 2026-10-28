import logging

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from prepza_common.ai import ai_usage
from prepza_common.ai.ai_constants import Outcome
from prepza_common.ai.llm import estimated_input
from prepza_common.ai.tracing import hiding, new_trace_id, traced

from assistant.config import settings
from assistant.constants.ai_usage import MESSAGE_ACTION
from assistant.constants.tool_groups import CORE_TOOLS, MAX_GROUPS, ROUTING_MESSAGES, TOOL_GROUPS
from assistant.integrations import llm
from assistant.models.answers import Answer, Turn
from assistant.prompts.tool_routing import TOOL_ROUTING_INPUT, TOOL_ROUTING_SYSTEM
from assistant.schemas.tool_routing import ToolRoute

logger = logging.getLogger(__name__)
CONTEXT_END = "</context>"


def routing_prompt(messages: list[BaseMessage]) -> list[BaseMessage]:
    """The new message (its turn's context apart: the page is the part routing needs) and the
    conversation's last few messages before it, as data."""
    context, _, message = str(messages[-1].content).rpartition(CONTEXT_END)
    earlier = "\n".join(
        f"{item.type}: {item.content}" for item in messages[1:-1][-ROUTING_MESSAGES:]
    )
    text = TOOL_ROUTING_INPUT.format(earlier=earlier, page=context, message=message.strip())

    return [SystemMessage(content=TOOL_ROUTING_SYSTEM), HumanMessage(content=text)]


def offered(route: ToolRoute) -> frozenset[str]:
    names = set(CORE_TOOLS)

    for group in route.groups[:MAX_GROUPS]:
        names |= TOOL_GROUPS[group]

    return frozenset(names)


async def routed_tools(messages: list[BaseMessage], turn: Turn, answer: Answer):
    """The tools this turn is offered: the core ones and the groups the routing call picks for
    the message; None (every tool) when the call fails, so a turn never loses a tool to it.
    Its tokens count with the answer's."""
    prompt = routing_prompt(messages)
    usage = {"input_tokens": estimated_input(prompt), "output_tokens": 0}
    outcome = Outcome.OK
    names = None
    # The answer's one Langfuse trace, which its model calls report to.
    answer.trace_id = answer.trace_id or new_trace_id()

    try:
        with hiding(turn.user_name):
            config = traced(answer.trace_id, str(turn.conversation_id))
            result = (
                await llm.get_routing_model()
                .with_structured_output(ToolRoute, include_raw=True)
                .ainvoke(prompt, config)
            )
        usage = result["raw"].usage_metadata or usage
        names = offered(result["parsed"]) if result["parsed"] else None
    except Exception as failure:  # noqa: BLE001 - every tool is offered instead
        logger.warning("Routing a turn's tools failed: %s", type(failure).__name__)
        outcome = Outcome.FAILED

    answer.input_tokens += usage["input_tokens"]
    answer.output_tokens += usage["output_tokens"]
    await ai_usage.record(
        MESSAGE_ACTION,
        settings.routing_model,
        usage,
        company_id=turn.company_id,
        user_id=turn.user_id,
        subject_id=turn.conversation_id,
        outcome=outcome,
    )

    return names
