"""The tools against the running stack's services, as a throwaway Auth emulator user."""

import uuid

from assistant.services.tool_calls import call_tool


def test_a_tool_calls_companies_as_the_user(run, token):
    companies = run(call_tool("list_companies", {}, token, "en", None))
    pause = run(call_tool("get_pause", {}, token, "en", None))

    # A new user has no companies yet.
    assert (companies.status_code, companies.content) == (
        200,
        {"data": [], "source": "list_companies"},
    )
    assert pause.content["data"] == {"paused": False}


def test_another_companys_data_is_refused_by_companies(run, token):
    result = run(call_tool("get_company", {"company_id": str(uuid.uuid4())}, token, "de", None))

    assert result.status_code in (403, 404)
    assert result.content["error"] == result.status_code
    assert result.content["detail"]


def test_a_forged_token_is_refused_downstream(run):
    result = run(call_tool("list_companies", {}, "forged", "en", None))

    assert result.status_code == 401


def test_a_page_id_that_isnt_the_users_gets_a_404_from_the_tools(run, token):
    """The page's ids are only context: a tool reads with the user's token, so an interview or a
    candidate that isn't theirs is refused there."""
    interview, invite = str(uuid.uuid4()), str(uuid.uuid4())
    found = run(call_tool("get_interview", {"interview_id": interview}, token, "en", None))
    arguments = {"interview_id": interview, "invite_id": invite}
    scorecard = run(call_tool("get_scorecard", arguments, token, "en", None))

    assert (found.status_code, scorecard.status_code) == (404, 404)
