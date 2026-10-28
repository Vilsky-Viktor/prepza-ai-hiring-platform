import asyncio
import uuid

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from assistant.constants.tool_groups import CORE_TOOLS, MAX_GROUPS, TOOL_GROUPS, ToolGroup
from assistant.integrations import llm
from assistant.models.answers import Answer, Turn
from assistant.services.chat import converse
from assistant.services.registry import tools
from assistant.services.tool_routing import routed_tools
from tests.fake_model import FakeModel, text

TURN = Turn(uuid.uuid4(), "ann", None, "user-token", "en", frozenset(), "Ann Lee")
MESSAGES = [
    SystemMessage(content="system"),
    HumanMessage(content="Invite lena@example.com."),
    AIMessage(content="Which interview?"),
    HumanMessage(content='<context>\n- the page "interviews"\n</context>\n\nThe second one.'),
]


def route(messages=MESSAGES):
    answer = Answer()

    return asyncio.run(routed_tools(messages, TURN, answer)), answer


def test_every_tool_is_in_the_core_or_in_exactly_one_group():
    grouped = [name for names in TOOL_GROUPS.values() for name in names]

    assert len(grouped) == len(set(grouped))
    assert not CORE_TOOLS & set(grouped)
    assert set(tools()) == CORE_TOOLS | set(grouped)


def test_a_turn_is_offered_the_core_tools_and_the_groups_picked(routing):
    routing.groups = [ToolGroup.CANDIDATES]
    names, answer = route()

    assert names == CORE_TOOLS | TOOL_GROUPS[ToolGroup.CANDIDATES]
    # Its tokens count with the answer's.
    assert (answer.input_tokens, answer.output_tokens) == (7, 3)


def test_no_more_than_two_groups_are_offered(routing):
    routing.groups = list(ToolGroup)
    names, _ = route()
    first = list(ToolGroup)[:MAX_GROUPS]

    assert names == CORE_TOOLS.union(*(TOOL_GROUPS[group] for group in first))


def test_routing_reads_the_message_with_the_conversation_and_the_page_as_data(routing):
    route()
    [prompt] = routing.prompts
    text = prompt[1].content

    assert "human: Invite lena@example.com." in text
    assert "ai: Which interview?" in text
    assert '<page><context>\n- the page "interviews"\n</page>' in text
    assert text.endswith("<message>\nThe second one.\n</message>")
    # The instructions stay the same for every message.
    assert "lena" not in prompt[0].content


def test_a_failed_routing_call_offers_every_tool(routing):
    routing.error = TimeoutError("slow")
    names, answer = route()

    assert names is None
    assert answer.input_tokens > 0


def test_the_model_is_offered_only_the_routed_tools(routing, monkeypatch):
    routing.groups = [ToolGroup.BILLING]
    model = FakeModel(text("Done."))
    monkeypatch.setattr(llm, "get_chat_model", lambda: model)
    asyncio.run(converse(list(MESSAGES), TURN, Answer(), lambda event: None))

    [(definitions, _)] = model.bound
    offered = {definition["function"]["name"] for definition in definitions}
    assert offered == CORE_TOOLS | TOOL_GROUPS[ToolGroup.BILLING] | {"sign_out", "show"}
