"""A delegated turn (ASSISTANT_MODE=subagents) through chat.converse with a scripted model: the
domain agent works from the brief with its own tools only, as the user; its cards reach the
panel unchanged and its text only the main agent; a brief naming another company is refused;
its calls report under a span of the turn's trace."""

import asyncio
import json
import uuid
from contextlib import contextmanager

import httpx
import pytest
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from app.config.settings import settings
from app.constants.actions_flow import PENDING_FOR_MODEL
from app.constants.subagents import DOMAINS, AssistantMode
from app.integrations import llm, services
from app.models.answers import Answer, Turn
from app.models.tools import ToolResult
from app.services import chat, subagents
from tests.fake_model import FakeModel, calls, text

COMPANY = "8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f"
TURN = Turn(uuid.uuid4(), "ann", uuid.UUID(COMPANY), "user-token", "en", frozenset({COMPANY}))
INVITE = {"interview_id": "i-1", "email": "a@example.com"}
BRIEF = {"task": "Invite a@example.com", "company_id": COMPANY, "interview_id": "i-1"}


@pytest.fixture
def model(monkeypatch):
    monkeypatch.setattr(settings, "assistant_mode", AssistantMode.SUBAGENTS)
    fake = FakeModel()
    monkeypatch.setattr(llm, "get_chat_model", lambda: fake)

    return fake


@pytest.fixture
def prepared(monkeypatch):
    """Actions prepared as the user, each a card waiting for Confirm."""
    made = []

    async def prepare(tool, arguments, turn, seen=None):
        made.append((tool.name, arguments, turn.token))
        block = {"kind": "action", "action_id": f"a-{len(made)}"}

        content = {"pending_confirmation": True, "detail": PENDING_FOR_MODEL}

        return ToolResult(tool.name, arguments, None, content, block, 0, uuid.uuid4())

    monkeypatch.setattr(chat, "prepare", prepare)

    return made


@pytest.fixture
def gets(monkeypatch):
    async def get(service, path, query, token, language, via=None):
        return httpx.Response(200, json=[], request=httpx.Request("GET", "http://service"))

    monkeypatch.setattr(services, "get", get)


def run(model, *replies):
    model.replies = list(replies)
    events, answer = [], Answer()
    prompt = [
        SystemMessage(content='Rules\n\nContext:\n- The user\'s name is "Ann".'),
        HumanMessage(content="Invite a@example.com to Data Analyst"),
    ]
    asyncio.run(chat.converse(prompt, TURN, answer, events.append))

    return events, answer


def offered(model, call: int) -> list[str]:
    tools, _ = model.bound[call]

    return [tool["function"]["name"] for tool in tools]


def test_a_domain_agent_prepares_the_card_and_the_turn_ends_with_it(model, prepared):
    events, answer = run(
        model, calls(("delegate_candidates", BRIEF)), calls(("invite_candidate", INVITE))
    )

    # The main agent has delegates, the domain agent its own tools.
    assert "delegate_candidates" in offered(model, 0)
    assert sorted(offered(model, 1)) == sorted(
        [*DOMAINS["candidates"]["tools"], *DOMAINS["candidates"]["shared"], "show"]
    )
    # The domain agent read the conversation and the brief, with the ids.
    system, user, brief = model.prompts[1]
    assert system.content.startswith("You manage the candidates")
    assert user.content == "Invite a@example.com to Data Analyst"
    assert "Invite a@example.com" in brief.content and "i-1" in brief.content
    assert prepared == [("invite_candidate", INVITE, "user-token")]
    # Its card reached the panel unchanged, and says it all: nobody is asked again.
    assert {"block": {"kind": "action", "action_id": "a-1"}} in events
    assert len(model.prompts) == 2
    assert len(answer.pending) == 1
    # Each model call's tokens, the domain agent's too; the delegate kept without its brief.
    assert (answer.input_tokens, answer.output_tokens) == (20, 10)
    assert [(result.tool, result.arguments) for result in answer.results] == [
        ("delegate_candidates", {})
    ]


def test_the_main_agent_reads_a_domain_agents_reply_the_user_doesnt(model, prepared, gets):
    events, answer = run(
        model,
        calls(("delegate_candidates", BRIEF)),
        calls(("list_interviews", {"company_id": COMPANY})),
        text("Which interview: Store Manager or Field Technician?"),
        text("Which interview?"),
    )

    [reply] = [m for m in model.prompts[3] if isinstance(m, ToolMessage)]
    assert json.loads(reply.content) == {
        "reply": "Which interview: Store Manager or Field Technician?",
        "cards_shown": 0,
    }
    assert [event["delta"] for event in events if "delta" in event] == ["Which", " interview?"]
    assert answer.content == "Which interview?"
    assert [result.tool for result in answer.results] == ["list_interviews", "delegate_candidates"]


def test_independent_parts_go_to_their_domains_at_once(model, prepared):
    member = {"task": "Add b@example.com as a viewer", "company_id": COMPANY, "interview_id": None}
    scripts = {
        "Rules": [calls(("delegate_candidates", BRIEF), ("delegate_company", member))],
        "You manage the candidates": [calls(("invite_candidate", INVITE))],
        "You manage a company's profile": [
            calls(("invite_member", {"email": "b@example.com", "role": "viewer"}))
        ],
    }
    script_of = FakeModel.astream

    async def astream(messages, config=None):
        start = next(key for key in scripts if messages[0].content.startswith(key))
        model.replies = [scripts[start].pop(0)]

        async for chunk in script_of(model, messages, config):
            yield chunk

    model.astream = astream
    prompt = [
        SystemMessage(content="Rules\n\nContext:\n- Today."),
        HumanMessage(content="Invite a@example.com and add b@example.com to the team"),
    ]
    answer = Answer()
    asyncio.run(chat.converse(prompt, TURN, answer, lambda event: None))

    assert sorted(name for name, _, _ in prepared) == ["invite_candidate", "invite_member"]
    assert len(answer.pending) == 2
    assert all(not script for script in scripts.values())


def test_a_domain_agent_cant_call_another_domains_tool(model, prepared):
    run(
        model,
        calls(("delegate_candidates", BRIEF)),
        calls(("delete_company", {"company_id": COMPANY})),
        text("I can't."),
        text("Done."),
    )

    assert prepared == []
    refused = [m for m in model.prompts[2] if isinstance(m, ToolMessage)]
    assert json.loads(refused[0].content)["error"] == 404


def test_a_brief_naming_another_company_runs_nothing(model, prepared):
    other = {**BRIEF, "company_id": str(uuid.uuid4())}
    _, answer = run(model, calls(("delegate_candidates", other)), text("Not found."))

    # The main agent was asked twice; no domain agent ran.
    assert len(model.prompts) == 2
    [reply] = [m for m in model.prompts[1] if isinstance(m, ToolMessage)]
    assert json.loads(reply.content)["error"] == 404
    assert answer.results[0].status_code is None


def test_single_mode_has_no_delegates(model, prepared, monkeypatch):
    monkeypatch.setattr(settings, "assistant_mode", AssistantMode.SINGLE)
    run(model, calls(("delegate_candidates", BRIEF)), text("Hm."))

    assert "invite_candidate" in offered(model, 0)
    assert "delegate_candidates" not in offered(model, 0)
    assert len(model.prompts) == 2


def test_a_domain_agents_calls_report_under_its_span(model, prepared, monkeypatch):
    spans = []

    @contextmanager
    def child_span(trace_id, name):
        spans.append((trace_id, name))
        yield "span-1"

    monkeypatch.setattr(chat, "new_trace_id", lambda: "t" * 32)
    monkeypatch.setattr(chat, "traced", lambda trace_id, span_id: {"t": trace_id, "s": span_id})
    monkeypatch.setattr(subagents, "child_span", child_span)
    run(model, calls(("delegate_candidates", BRIEF)), text("Ready."), text(""))

    assert spans == [("t" * 32, "delegate_candidates")]
    assert [config["s"] for config in model.configs] == [None, "span-1", None]
