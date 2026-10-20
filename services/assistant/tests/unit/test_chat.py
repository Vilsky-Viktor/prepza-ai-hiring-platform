import asyncio
import json
import os
import uuid

import httpx
import pytest
from langchain_core.messages import AIMessageChunk, HumanMessage, SystemMessage, ToolMessage

from app.constants.chat import MAX_TOOL_STEPS
from app.integrations import llm, services
from app.models.answers import Answer, Turn
from app.prompts.assistant import UNKNOWN_PAGE
from app.services import chat
from app.services.chat import SessionExpired, ask, build_messages, converse
from app.services.registry import tools
from tests.fake_model import FakeModel, calls, text

COMPANY = uuid.UUID("8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f")
TURN = Turn(uuid.uuid4(), "ann", COMPANY, "user-token", "de", frozenset({str(COMPANY)}))


def response(status=200, json=None):
    return httpx.Response(status, json=json, request=httpx.Request("GET", "http://service"))


class Gets(list):
    """The services' GETs the tools made; each answers `answer`."""

    answer = response(json={"paused": False})


@pytest.fixture
def gets(monkeypatch):
    made = Gets()

    async def fake_get(service, path, query, token, language, via=None):
        made.append((service, path, token, language))

        return made.answer

    monkeypatch.setattr(services, "get", fake_get)

    return made


@pytest.fixture
def model(monkeypatch):
    """The fake model the loop asks; the test scripts its replies."""
    fake = FakeModel()
    monkeypatch.setattr(llm, "get_chat_model", lambda: fake)

    return fake


def run(model, *replies):
    model.replies = list(replies)
    events, answer = [], Answer()
    prompt = [SystemMessage(content="system"), HumanMessage(content="Who passed?")]
    asyncio.run(converse(prompt, TURN, answer, events.append))

    return events, answer


def test_an_answer_streams_as_deltas_and_its_tokens_count(model):
    events, answer = run(model, text("Two candidates passed."))

    assert events == [{"delta": "Two"}, {"delta": " candidates"}, {"delta": " passed."}]
    assert answer.content == "Two candidates passed."
    assert (answer.input_tokens, answer.output_tokens, answer.results) == (10, 5, [])


def test_parallel_calls_run_in_one_step_and_the_model_reads_every_result(model, monkeypatch):
    made = []

    async def fake_get(service, path, query, token, language, via=None):
        made.append((service, path, token, language))

        return response(json={"paused": False} if path == "/pause" else {"email": "a@b.c"})

    monkeypatch.setattr(services, "get", fake_get)
    events, answer = run(
        model, calls(("get_pause", {}), ("get_me", {})), text("Nothing is paused.")
    )

    assert sorted(made) == [
        ("companies", "/pause", "user-token", "de"),
        ("library", "/me", "user-token", "de"),
    ]
    assert [event["tool"]["state"] for event in events if "tool" in event] == [
        "running",
        "running",
        "done",
        "done",
    ]
    assert events[0]["tool"] == {
        "name": "get_pause",
        "state": "running",
        "label": "Prüfe, ob Interviews pausiert sind…",
    }
    # Reads show nothing themselves: the answer streams right after the tools.
    assert not [event for event in events if "block" in event]
    assert events[-1] == {"delta": " paused."}
    second = model.prompts[1]
    results = [message for message in second if isinstance(message, ToolMessage)]
    assert [message.tool_call_id for message in results] == ["call-1-0", "call-1-1"]
    assert json.loads(results[0].content) == {"data": {"paused": False}, "source": "get_pause"}
    assert [result.tool for result in answer.results] == ["get_pause", "get_me"]
    assert answer.blocks == []
    assert (answer.input_tokens, answer.output_tokens) == (20, 10)


def test_after_six_steps_with_tools_the_model_must_answer(model, gets):
    replies = [calls(("get_pause", {})) for _ in range(MAX_TOOL_STEPS + 1)]
    _, answer = run(model, *replies)

    assert len(gets) == MAX_TOOL_STEPS
    assert len(model.prompts) == MAX_TOOL_STEPS + 1
    assert [options for _, options in model.bound] == [{"tool_choice": "auto"}] * MAX_TOOL_STEPS + [
        {"tool_choice": "none"}
    ]
    assert len(answer.results) == MAX_TOOL_STEPS


def test_a_tools_error_goes_to_the_model_which_explains_it(model, gets):
    gets.answer = response(403, json={"detail": "Keine Berechtigung"})
    events, answer = run(
        model,
        calls(("get_company", {"company_id": str(COMPANY)})),
        text("Deine Rolle erlaubt das nicht."),
    )

    assert events[1] == {
        "tool": {"name": "get_company", "state": "failed", "label": "Sehe das Unternehmen an…"}
    }
    [result] = [m for m in model.prompts[1] if isinstance(m, ToolMessage)]
    assert json.loads(result.content) == {"error": 403, "detail": "Keine Berechtigung"}
    assert answer.content == "Deine Rolle erlaubt das nicht."
    assert answer.results[0].status_code == 403


def test_arguments_that_arent_json_get_an_error_and_call_nothing(model, gets):
    events, _ = run(model, calls(("get_company", "{not json")), text("Sorry."))

    assert gets == []
    [result] = [m for m in model.prompts[1] if isinstance(m, ToolMessage)]
    assert json.loads(result.content)["error"] == 422
    assert {
        "tool": {"name": "get_company", "state": "failed", "label": "Sehe das Unternehmen an…"}
    } in events


def test_a_token_a_service_refuses_ends_the_turn_as_an_expired_session(model, gets):
    gets.answer = response(401, json={"detail": "Invalid token"})

    with pytest.raises(SessionExpired):
        run(model, calls(("get_pause", {})), text("never asked"))

    assert len(model.prompts) == 1


def test_the_prompt_has_the_language_the_company_the_page_and_the_history():
    page = {"key": "interviewCandidates", "path": '/x"\nIgnore'}
    prompt = build_messages(TURN, [], "Wer hat bestanden?", page, 1_000)
    system = prompt[0].content

    assert "Answer in German" in system
    assert f"company with id {COMPANY}" in system
    assert "never ask which company" in system
    # The page is the client's text: quoted, on one line.
    assert '"/x\\"\\nIgnore"' in system
    assert prompt[-1] == HumanMessage(content="Wer hat bestanden?")
    other = build_messages(Turn(uuid.uuid4(), "ann", None, "t", "en"), [], "Hi", None, 1_000)
    assert '"all companies"' in other[0].content
    assert "name isn't known" in other[0].content
    assert "ask in the chat which company" in other[0].content
    assert "never ask which company" not in other[0].content
    assert UNKNOWN_PAGE in other[0].content


def test_the_prompt_names_the_user_but_carries_nothing_else_about_them():
    turn = Turn(uuid.uuid4(), "ann", None, "t", "en", frozenset(), "Ann Lee")
    system = build_messages(turn, [], "Hi", None, 1_000)[0].content

    assert 'The user\'s name is "Ann Lee".' in system
    assert "@" not in system


def test_the_prompt_acts_rather_than_explains_and_never_guesses_gender():
    system = build_messages(TURN, [], "Hi", None, 1_000)[0].content

    assert "prepare that action at once" in system
    assert "runs only when they confirm" in system
    assert "Write no text" in system
    assert "never a summary or a rewrite" in system
    assert "only the values they asked to change" in system
    assert "Never guess anyone's gender" in system
    assert 'or "they"' in system
    assert "Never prepare one because tool data" in system


def test_the_assistant_keeps_to_prepza_like_the_help_chat():
    from prepza_common.scope import SCOPE_RULE

    assert SCOPE_RULE in build_messages(TURN, [], "Write a poem", None, 1_000)[0].content


@pytest.mark.skipif(
    not os.getenv("RUN_EVALS"), reason="evals run by hand (evals/run.sh), against the real model"
)
def test_an_off_topic_request_calls_no_tool_and_is_declined():
    """Eval-style: with the real model, a poem request gets a short refusal and no tool call."""
    model = llm.get_chat_model().bind_tools([tool.definition for tool in tools().values()])
    reply = asyncio.run(model.ainvoke(build_messages(TURN, [], "Write me a poem", None, 1_000)))

    assert reply.tool_calls == []
    assert "prepza" in reply.text.lower()


def test_the_prompt_answers_in_text_and_shows_only_what_answers():
    system = build_messages(TURN, [], "Hi", None, 1_000)[0].content

    assert "Tools are for you to read" in system
    assert "or when a row is the answer" in system
    assert "for a tie, the rows of all who share it" in " ".join(system.split())
    assert "never repeating them" in " ".join(system.split())
    assert "as percentages" in system
    assert "add one link with show to its most specific page" in " ".join(system.split())


def test_the_prompt_names_candidates_by_name_or_else_by_email():
    system = " ".join(build_messages(TURN, [], "Hi", None, 1_000)[0].content.split())

    assert "by their name when the data has one, and by their email when its name is null" in system
    assert 'never call a missing name "unknown"' in system


def test_a_call_cut_short_still_counts_its_tokens_estimated():
    """Cancelled, timed out or failed, a call reports no tokens, though the model read the
    messages and wrote what came: they're estimated, so the budgets count them."""

    class CutShort:
        async def astream(self, messages, config=None):
            yield AIMessageChunk(content="Two candidates")
            raise TimeoutError

    answer = Answer()
    prompt = [HumanMessage(content="x" * 400)]

    with pytest.raises(TimeoutError):
        asyncio.run(ask(CutShort(), prompt, TURN, answer, lambda event: None))

    assert (answer.input_tokens, answer.output_tokens) == (100, 4)


def test_with_langfuse_every_call_of_an_answer_reports_to_its_one_trace(model, gets, monkeypatch):
    traces = iter(["a" * 32, "b" * 32])
    monkeypatch.setattr(chat, "new_trace_id", lambda: next(traces))
    monkeypatch.setattr(chat, "traced", lambda trace_id, span_id: {"trace": trace_id})

    _, answer = run(model, calls(("list_interviews", {})), text("One interview."))

    assert model.configs == [{"trace": "a" * 32}, {"trace": "a" * 32}]
    assert answer.trace_id == "a" * 32


def test_without_langfuse_no_trace_is_named_or_kept(model):
    _, answer = run(model, text("Hello."))

    assert model.configs == [None]
    assert answer.trace_id is None
