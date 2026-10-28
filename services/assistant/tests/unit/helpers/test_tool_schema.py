from assistant.helpers.tool_schema import parameter_schema, resolve

COMPONENTS = {
    "Sort": {"type": "string", "enum": ["grade", "date"], "title": "Sort"},
    "Filter": {"$ref": "#/components/schemas/Sort"},
}


def test_refs_and_optional_values_resolve_to_their_schema():
    optional = {"anyOf": [{"$ref": "#/components/schemas/Filter"}, {"type": "null"}], "title": "F"}

    assert resolve(optional, COMPONENTS)["enum"] == ["grade", "date"]
    assert resolve({"anyOf": [{"type": "string"}, {"type": "integer"}]}, COMPONENTS)["anyOf"]


def test_a_parameter_keeps_only_what_the_model_needs():
    parameter = {
        "name": "limit",
        "description": "Number of items",
        "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 100, "title": "L"},
    }

    assert parameter_schema(parameter, COMPONENTS) == {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "description": "Number of items",
    }
