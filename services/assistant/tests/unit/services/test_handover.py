import asyncio
import uuid

import httpx
import pytest
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from assistant.constants.chat import HANDOVER
from assistant.helpers.handover import failed_on_our_side, with_handover
from assistant.integrations import llm, services
from assistant.models.answers import Answer, Turn
from assistant.models.tools import ToolResult
from assistant.services.chat import converse
from tests.fake_model import FakeModel, calls, text

COMPANY = uuid.UUID("8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f")
TURN = Turn(uuid.uuid4(), "ann", COMPANY, "user-token", "en", frozenset({str(COMPANY)}))


def result(status_code, content=None) -> ToolResult:
    return ToolResult("get_company", {}, status_code, content or {}, None, 0)


@pytest.mark.parametrize(
    ("status_code", "content", "failed"),
    [
        (None, {"error": 503}, True),
        (None, {"error": 504}, True),
        (500, {"error": 500}, True),
        (502, {"error": 502}, True),
        # The model's own mistakes and answers that are the data: not testee failing.
        (None, {"error": 422}, False),
        (None, {"error": 404}, False),
        (404, {"error": 404}, False),
        (403, {"error": 403}, False),
        (200, {"data": []}, False),
    ],
)
def test_only_a_service_that_failed_counts(status_code, content, failed):
    assert failed_on_our_side(result(status_code, content)) is failed


def test_the_first_failure_hands_over_once_on_the_last_reply():
    replies = [
        ToolMessage(content="a", tool_call_id="1"),
        ToolMessage(content="b", tool_call_id="2"),
    ]
    down = result(None, {"error": 503})

    handed = with_handover(replies, [], [result(200), down])

    assert [reply.content for reply in handed] == ["a", f"b\n\n{HANDOVER}"]
    assert handed[1].tool_call_id == "2"
    # Told once a turn: a later step's failure adds nothing.
    assert with_handover(replies, [down], [down]) == replies
    assert with_handover(replies, [], [result(200)]) == replies


def test_a_turn_whose_service_fails_tells_the_model_to_hand_over(monkeypatch):
    model = FakeModel()
    monkeypatch.setattr(llm, "get_chat_model", lambda: model)

    async def unavailable(*args, **kwargs):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(services, "get", unavailable)
    model.replies = [
        calls(("get_company", {"company_id": str(COMPANY)})),
        text("That didn't work."),
    ]
    prompt = [SystemMessage(content="system"), HumanMessage(content="Which plan am I on?")]
    asyncio.run(converse(prompt, TURN, Answer(), lambda event: None))

    [reply] = [m for m in model.prompts[1] if isinstance(m, ToolMessage)]
    assert reply.content.endswith(HANDOVER)
