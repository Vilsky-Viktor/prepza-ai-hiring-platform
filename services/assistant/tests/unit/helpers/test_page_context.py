import asyncio
import uuid

import httpx
import pytest
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import ValidationError

from assistant.constants.chat import MAX_PAGE_LENGTH
from assistant.helpers.history import history
from assistant.helpers.page_context import describe_page
from assistant.integrations import services
from assistant.models.answers import Turn
from assistant.models.conversations import Message
from assistant.schemas.chat import ChatRequest, PageContext
from assistant.services.chat import build_messages
from assistant.services.registry import tools
from assistant.services.tool_calls import call_tool

COMPANY = "8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f"
INTERVIEW = "1f2e3d4c-5b6a-4978-8a9b-0c1d2e3f4a5b"
PAGE = {
    "key": "interviewCandidates",
    "path": f"/companies/{COMPANY}/interviews/{INTERVIEW}?tab=candidates",
    "company_id": COMPANY,
    "interview_id": INTERVIEW,
}
TURN = Turn(uuid.uuid4(), "ann", uuid.UUID(COMPANY), "user-token", "en", frozenset({COMPANY}))


def test_the_page_line_names_the_page_its_tab_and_each_id():
    prompt = build_messages(TURN, [], "Who's best here?", PAGE, 1_000)
    context = prompt[-1].content

    assert 'the page "interviewCandidates"' in context
    # The path with its query (the tab), quoted: it's the client's text, never an instruction.
    assert f'"{PAGE["path"]}"' in context
    assert PAGE["path"] not in prompt[0].content
    assert f"the company with id {COMPANY}" in context
    assert f"the interview with id {INTERVIEW}" in context
    assert "get_page_guide" in prompt[0].content


def test_a_page_without_a_key_or_ids_is_its_path_alone():
    assert describe_page({"path": "/somewhere"}) == 'at "/somewhere"'


def test_each_earlier_question_starts_with_the_page_it_was_asked_on():
    rows = [
        Message(id=uuid.uuid4(), role="user", content="Who's best here?", page=PAGE),
        Message(id=uuid.uuid4(), role="assistant", content="Ann.", page=None),
        Message(id=uuid.uuid4(), role="user", content="Thanks", page=None),
    ]

    [asked, answered, plain] = history(rows, 1_000, with_pages=True)

    assert asked.content.startswith(f"[Asked on {describe_page(PAGE)}]")
    assert asked.content.endswith("Who's best here?")
    assert answered == AIMessage(content="Ann.")
    assert plain == HumanMessage(content="Thanks")
    # Titles and AI apps read the text alone.
    assert history(rows, 1_000)[0] == HumanMessage(content="Who's best here?")


def test_an_unknown_key_is_dropped_and_a_long_path_is_cut():
    page = PageContext(key="superadmin", path="/x" * MAX_PAGE_LENGTH)

    assert page.key is None
    assert len(page.path) == MAX_PAGE_LENGTH
    assert PageContext(key="billing", path="/").key == "billing"


@pytest.mark.parametrize("field", ["company_id", "interview_id", "candidate_id", "template_id"])
def test_an_id_that_isnt_an_id_is_refused(field):
    with pytest.raises(ValidationError):
        PageContext(path="/", **{field: "../internal"})


def test_a_message_carries_its_page():
    body = ChatRequest(message="Hi", page=PAGE)

    assert body.page.model_dump(exclude_none=True) == PAGE


def test_the_page_guide_tool_reads_site_by_the_key(monkeypatch):
    asked = []

    async def get(service, path, query, token, language, via=None):
        asked.append((service, path, token, language))
        guide = {"key": "billing", "title": "Billing", "text": "t", "actions": [], "tips": []}

        return httpx.Response(200, json=guide, request=httpx.Request("GET", "http://site"))

    monkeypatch.setattr(services, "get", get)

    result = asyncio.run(call_tool("get_page_guide", {"key": "billing"}, "user-token", "de", None))

    assert asked == [("site", "/help/pages/billing", "user-token", "de")]
    assert result.content["data"]["title"] == "Billing"
    assert not tools()["get_page_guide"].confirm
