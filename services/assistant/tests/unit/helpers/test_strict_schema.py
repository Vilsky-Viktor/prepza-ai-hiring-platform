from assistant.constants.show import SHOW_DEFINITION
from assistant.helpers.arguments import problems
from assistant.helpers.strict_schema import strict_definition
from assistant.services.registry import tools


def tool(parameters: dict) -> dict:
    return {
        "type": "function",
        "function": {"name": "t", "description": "d", "parameters": parameters},
    }


def test_optional_parameters_become_required_and_nullable_and_the_tool_strict():
    definition = tool(
        {
            "type": "object",
            "properties": {
                "name": {"type": "string", "maxLength": 80},
                "status": {"type": "string", "enum": ["open", "closed"]},
            },
            "required": ["name"],
            "additionalProperties": False,
        }
    )
    function = strict_definition(definition)["function"]

    assert function["strict"] is True
    assert function["parameters"]["required"] == ["name", "status"]
    assert function["parameters"]["properties"]["name"] == {"type": "string"}
    assert function["parameters"]["properties"]["status"] == {
        "type": ["string", "null"],
        "enum": ["open", "closed", None],
    }
    # The original, which the code checks arguments against, keeps its limits.
    assert definition["function"]["parameters"]["properties"]["name"]["maxLength"] == 80


def test_a_free_map_of_values_keeps_the_tool_as_it_is():
    definition = tool(
        {
            "type": "object",
            "properties": {
                "values": {"type": "object", "additionalProperties": {"type": "boolean"}}
            },
            "required": [],
            "additionalProperties": False,
        }
    )

    assert strict_definition(definition) == definition


def test_objects_in_lists_are_strict_too():
    rows = strict_definition(SHOW_DEFINITION)["function"]["parameters"]["properties"]["rows"]
    row = rows["items"]

    assert rows["type"] == ["array", "null"]
    assert row["additionalProperties"] is False
    assert row["required"] == list(row["properties"])


def test_every_tool_but_a_free_map_is_strict_and_a_null_still_counts_as_left_out():
    found = {name: strict_definition(item.definition) for name, item in tools().items()}
    loose = [name for name, definition in found.items() if not definition["function"].get("strict")]

    assert loose == ["update_email_preferences"]

    for name, item in tools().items():
        nulls = {param: None for param in item.parameters["properties"]}
        required = set(item.parameters["required"])

        assert all("is required" in problem for problem in problems(nulls, item.parameters)), name
        assert len(problems(nulls, item.parameters)) == len(required), name
