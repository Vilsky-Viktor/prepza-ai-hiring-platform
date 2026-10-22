import pytest

from app.constants.tool_calls import FORBIDDEN_PATH_PREFIXES
from app.constants.tools import TOOLS
from app.constants.updates import GET_UPDATES
from app.services.registry import build, tools


def test_every_tool_resolves_in_its_services_snapshot():
    built = tools()

    assert set(built) == set(TOOLS) | {GET_UPDATES}
    assert {"search_candidates", "get_platform_guide", "get_api_settings"} <= set(built)


@pytest.mark.parametrize("name", sorted(TOOLS))
def test_every_tool_is_a_user_facing_read_or_a_write_the_user_confirms(name):
    entry = TOOLS[name]

    assert entry["method"] == "GET" or entry["confirm"] is True
    assert not entry["path"].startswith(FORBIDDEN_PATH_PREFIXES)


@pytest.mark.parametrize(
    "change, problem",
    [
        ({"method": "POST"}, "a POST needs confirm: True"),
        ({"method": "DELETE", "confirm": False}, "a DELETE needs confirm: True"),
        ({"method": "OPTIONS"}, "isn't allowed"),
        ({"path": "/internal/users/{user_id}"}, "not a user-facing route"),
        ({"path": "/superadmin/companies"}, "not a user-facing route"),
        ({"path": "/nowhere"}, "has no GET /nowhere"),
        ({"params": ["company_id", "nope"]}, "no parameter nope"),
        ({"params": []}, "required parameters not allowed"),
        ({"service": "elsewhere"}, "unknown service"),
    ],
)
def test_the_loader_refuses_what_the_assistant_must_not_call(change, problem):
    entry = {**TOOLS["get_company"], **change}

    with pytest.raises(ValueError, match=problem):
        build("get_company", entry)


def test_a_route_gone_from_the_snapshot_stops_the_start(monkeypatch):
    monkeypatch.setitem(TOOLS, "gone", {**TOOLS["get_pause"], "path": "/gone"})
    tools.cache_clear()

    try:
        with pytest.raises(ValueError, match="has no GET /gone"):
            tools()
    finally:
        monkeypatch.delitem(TOOLS, "gone")
        tools.cache_clear()


def test_parameters_keep_the_routes_types_enums_and_bounds():
    tool = tools()["list_candidates"]
    properties = tool.parameters["properties"]

    assert tool.path_params == ("interview_id",)
    assert tool.query_params == ("q", "status", "sort", "offset", "limit")
    assert tool.parameters["required"] == ["interview_id"]
    assert tool.parameters["additionalProperties"] is False
    assert properties["interview_id"] == {"type": "string", "format": "uuid"}
    assert properties["q"] == {"type": "string", "maxLength": 254}
    assert "finished" in properties["status"]["enum"]
    assert properties["sort"]["enum"] == ["grade", "date"]
    # `limit` is capped at what the model may read.
    assert properties["limit"]["maximum"] == tool.max_items == 20


def test_a_tool_is_described_by_its_route_or_its_override():
    built = tools()

    assert (
        built["get_platform_guide"]
        .definition["function"]["description"]
        .startswith("Everything prepza's help knows")
    )
    assert built["list_interviews"].definition["function"]["description"]
    assert built["get_api_settings"].path == "/manage"


def test_a_write_takes_its_body_fields_as_the_route_declares_them():
    tool = tools()["create_company"]

    assert (tool.method, tool.path, tool.confirm) == ("POST", "/companies", True)
    assert tool.body_params == ("name",)
    assert tool.parameters["required"] == ["name"]
    assert tool.parameters["properties"]["name"]["type"] == "string"


def test_a_write_refuses_a_body_field_its_route_lacks():
    entry = {**TOOLS["create_company"], "body": ["name", "nope"]}

    with pytest.raises(ValueError, match="the body has no field nope"):
        build("create_company", entry)


def test_candidates_are_read_with_their_names_and_invited_with_one():
    built = tools()

    for name in ("list_candidates", "search_candidates", "get_scorecard"):
        assert "name" in built[name].fields, name

    invite = built["invite_candidate"].parameters

    assert set(invite["properties"]) >= {"email", "name"}
    assert "name" not in invite["required"]


def test_a_topics_question_limit_isnt_capped_as_a_page_size():
    limit = tools()["set_topic_limit"].parameters["properties"]["limit"]

    assert limit.get("maximum", 1000) > 20
    assert "items to return" not in limit.get("description", "")
