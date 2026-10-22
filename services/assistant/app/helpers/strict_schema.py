import copy

# Keywords OpenAI's strict function calling refuses; the code checks them itself
# (helpers/arguments.py), so they're left out of what the model is given.
UNSUPPORTED = ("minLength", "maxLength", "propertyNames")


def strict_definition(definition: dict) -> dict:
    """A tool's definition with strict arguments: the model can only send what the schema
    allows. Every parameter is required, an optional one as nullable (a null counts as left
    out). A tool whose schema can't be strict (a free map of values) is given as it is."""
    function = definition["function"]

    if not can_be_strict(function["parameters"]):
        return definition

    parameters = strict_object(copy.deepcopy(function["parameters"]))

    return {**definition, "function": {**function, "parameters": parameters, "strict": True}}


def can_be_strict(schema: dict) -> bool:
    if isinstance(schema.get("additionalProperties"), dict):
        return False

    children = [*schema.get("properties", {}).values()]

    if isinstance(schema.get("items"), dict):
        children.append(schema["items"])

    return all(can_be_strict(child) for child in children)


def strict_object(schema: dict) -> dict:
    for keyword in UNSUPPORTED:
        schema.pop(keyword, None)

    if isinstance(schema.get("items"), dict):
        schema["items"] = strict_object(schema["items"])

    if schema.get("type") != "object":
        return schema

    required = set(schema.get("required", []))
    properties = schema.get("properties", {})

    for name, value in properties.items():
        properties[name] = strict_object(value)

        if name not in required:
            properties[name] = nullable(properties[name])

    schema["required"] = list(properties)
    schema["additionalProperties"] = False

    return schema


def nullable(schema: dict) -> dict:
    kind = schema.get("type")

    if isinstance(kind, str):
        schema["type"] = [kind, "null"]

    if "enum" in schema and None not in schema["enum"]:
        schema["enum"] = [*schema["enum"], None]

    return schema
