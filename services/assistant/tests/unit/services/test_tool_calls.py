import asyncio

import httpx
import pytest

from assistant.config import settings
from assistant.integrations import services
from assistant.services.registry import tools
from assistant.services.tool_calls import call_tool, call_tools, read

COMPANY = "8c1d2b8e-1a2b-4c3d-8e9f-0a1b2c3d4e5f"
INTERVIEW = "3f2b6a1e-8a7c-4c1e-9a55-0b6f3c2d1e00"


def answer(status=200, json=None, text=None, headers=None):
    request = httpx.Request("GET", "http://service")

    if json is not None:
        return httpx.Response(status, json=json, request=request)

    return httpx.Response(status, text=text or "", headers=headers, request=request)


class Calls(list):
    """The GETs made, and what the service answers (`answer`)."""

    answer = None


@pytest.fixture
def calls(monkeypatch):
    """Records each GET the tools make; the test sets what the service answers."""
    made = Calls()
    made.answer = answer(json=[])

    async def fake_get(service, path, query, token, language, via=None):
        made.append((service, path, query, token, language))
        found = made.answer

        if isinstance(found, Exception):
            raise found

        return found

    monkeypatch.setattr(services, "get", fake_get)

    return made


def run(name, arguments, company_id=COMPANY):
    return asyncio.run(call_tool(name, arguments, "user-token", "de", company_id))


def test_a_list_is_trimmed_and_cut_for_the_model_and_shows_nothing(calls):
    rows = [
        {"id": f"c{i}", "email": f"c{i}@example.com", "grade": 80, "passed": None, "secret": "x"}
        for i in range(4)
    ]
    calls.answer = answer(json=rows)
    result = run("list_candidates", {"interview_id": INTERVIEW, "status": "finished", "limit": 3})

    # One more than wanted, to tell whether there are more.
    assert calls == [
        (
            "companies",
            f"/interviews/{INTERVIEW}/candidates",
            {"status": "finished", "limit": 4},
            "user-token",
            "de",
        )
    ]
    assert result.status_code == 200
    assert result.content == {
        "data": [{"id": f"c{i}", "email": f"c{i}@example.com", "grade": 80} for i in range(3)],
        "source": "list_candidates",
        "shown": 3,
        "more": True,
        "narrow": result.content["narrow"],
    }
    # How to see the rest: the tool's own filters, never its paging or order.
    assert "q, status" in result.content["narrow"]
    assert "sort" not in result.content["narrow"]
    assert result.block is None


def test_a_paged_list_cut_short_points_to_its_next_page_and_to_the_user(calls):
    calls.answer = answer(json=[{"id": f"i{i}"} for i in range(6)])
    result = run("list_interviews", {"company_id": COMPANY, "offset": 10, "limit": 5})

    assert (result.content["shown"], result.content["more"]) == (5, True)
    # No filters of its own (the company is its scope): the next page, and the user to narrow it.
    assert "offset 15" in result.content["narrow"]
    assert "company_id" not in result.content["narrow"]


def test_the_model_gets_full_links_never_their_bare_codes(calls):
    site = settings.site_url.rstrip("/")
    calls.answer = answer(json={"id": "i1", "invite_token": "secret", "extra_time": 30})
    scorecard = run("get_scorecard", {"interview_id": INTERVIEW, "invite_id": COMPANY})

    assert scorecard.content["data"] == {
        "id": "i1",
        "extra_time": 30,
        "invite_url": f"{site}/invite/secret",
    }

    # A shareable link turned on, and an interview whose link is off.
    turned_on, _ = read(tools()["set_interview_link"], answer(json={"link_token": "job"}), 20)
    calls.answer = answer(json={"id": INTERVIEW, "title": "Backend", "link_token": None})
    without = run("get_interview", {"interview_id": INTERVIEW})

    assert turned_on["data"] == {"link_url": f"{site}/apply/job"}
    assert without.content["data"] == {"id": INTERVIEW, "title": "Backend"}


def test_the_credit_history_names_its_candidates_but_no_invoice(calls):
    entry = {
        "id": "e1",
        "amount": -100,
        "reason": "candidate",
        "invoice_id": "txn_1",
        "candidate": {"invite_id": "i1", "email": "c@example.com", "name": "Ann"},
    }
    calls.answer = answer(json=[entry])
    result = run("list_credit_history", {"company_id": COMPANY})

    assert result.content["data"] == [
        {
            "amount": -100,
            "reason": "candidate",
            "candidate": {"invite_id": "i1", "email": "c@example.com", "name": "Ann"},
        }
    ]


def test_a_limit_is_capped_at_the_tools_maximum_and_set_when_left_out(calls):
    run("list_interviews", {"company_id": COMPANY})

    assert calls[0][2] == {"company_id": COMPANY, "limit": 21}
    assert run("list_interviews", {"company_id": COMPANY, "limit": 50}).status_code is None


def test_the_platform_guide_is_read_whole_as_text(calls):
    guide = "<guide>\n" + "How prepza works. " * 2_000
    calls.answer = answer(text=guide, headers={"content-type": "text/plain"})
    result = run("get_platform_guide", {})

    assert calls[0][:3] == ("rounds", "/help/guide", {})
    assert result.content == {"data": guide, "source": "get_platform_guide"}
    assert result.block is None


def test_a_services_error_reaches_the_model_in_the_users_language(calls):
    calls.answer = answer(403, json={"detail": "Keine Berechtigung"})

    result = run("get_company", {"company_id": COMPANY})

    assert result.status_code == 403
    assert result.content == {"error": 403, "detail": "Keine Berechtigung"}
    assert result.block is None


def test_errors_without_a_message_name_their_status(calls):
    calls.answer = answer(422, json={"detail": [{"msg": "bad"}]})
    assert run("get_pause", {}).content["error"] == 422

    calls.answer = answer(502, text="<html>")
    assert run("get_pause", {}).content == {"error": 502, "detail": "Bad Gateway"}


@pytest.mark.parametrize(
    "error, status",
    [(httpx.ReadTimeout("slow"), 504), (httpx.ConnectError("down"), 503)],
)
def test_a_service_that_doesnt_answer_is_an_error_too(calls, error, status):
    calls.answer = error
    result = run("get_pause", {})

    assert result.status_code is None
    assert result.content["error"] == status
    assert result.content["detail"]


def test_refused_arguments_and_unknown_tools_call_nothing(calls):
    bad = run("get_company", {"company_id": "../internal/users"})
    unknown = run("drop_everything", {"company_id": COMPANY})

    assert calls == []
    assert bad.content["error"] == 422
    assert "company_id must be a UUID" in bad.content["detail"]
    assert unknown.content["error"] == 404


def test_a_steps_calls_run_at_most_four_at_a_time_in_order(monkeypatch):
    running, most = 0, 0

    async def fake_get(service, path, query, token, language, via=None):
        nonlocal running, most
        running += 1
        most = max(most, running)
        await asyncio.sleep(0.01)
        running -= 1

        return answer(json={"paused": False})

    monkeypatch.setattr(services, "get", fake_get)
    names = ["get_pause"] * 7 + ["get_me"]
    results = asyncio.run(call_tools([(name, {}) for name in names], "t", "en", None))

    assert most == 4
    assert [result.tool for result in results] == names


def test_a_write_answered_without_a_body_reads_as_nothing():
    tool = tools()["delete_interview"]
    response = httpx.Response(
        204,
        headers={"content-type": "application/json"},
        request=httpx.Request("DELETE", "http://x"),
    )

    assert read(tool, response, 20)[1] is None


def test_a_topics_questions_tell_the_model_which_are_multi_answer(calls):
    options = [{"answer": "a", "correct": True}, {"answer": "b", "correct": True}]
    question = {"id": "q1", "text": "Which?", "options": options, "multi": True, "likes": 0}
    calls.answer = answer(json=[question | {"position": 3}])
    result = run("list_topic_questions", {"interview_id": INTERVIEW, "topic_id": COMPANY})

    assert result.content["data"] == [question]
