from app.constants.tool_calls import FORBIDDEN_PATH_PREFIXES, WRITE_METHODS

# What a parameter's schema keeps for the model; the rest (titles, defaults) is noise.
KEPT_KEYWORDS = (
    "type",
    "enum",
    "format",
    "maxLength",
    "minLength",
    "minimum",
    "maximum",
    "minItems",
    "maxItems",
)


def check_route(name: str, entry: dict) -> None:
    """Refuses an allow-list entry the assistant must never call: a write that doesn't wait for
    the user's confirmation, and other services' or prepza's own team's routes."""
    if entry["method"] not in WRITE_METHODS + ("GET",):
        raise ValueError(f"Tool {name}: method {entry['method']} isn't allowed")

    if entry["method"] != "GET" and entry.get("confirm") is not True:
        raise ValueError(f"Tool {name}: a {entry['method']} needs confirm: True")

    if entry["path"].startswith(FORBIDDEN_PATH_PREFIXES):
        raise ValueError(f"Tool {name}: {entry['path']} is not a user-facing route")


def resolve(schema: dict, components: dict) -> dict:
    """The schema a $ref points to, and the non-null choice of an optional one."""
    if "$ref" in schema:
        return resolve(components[schema["$ref"].rsplit("/", 1)[-1]], components)

    choices = [choice for choice in schema.get("anyOf", []) if choice.get("type") != "null"]

    if len(choices) == 1:
        return resolve(
            {**choices[0], **{k: v for k, v in schema.items() if k != "anyOf"}}, components
        )

    return schema


def kept_schema(schema: dict, components: dict) -> dict:
    """A value's schema as the model needs it: its keywords, and a list's items or an object's
    values, resolved the same way."""
    schema = resolve(schema, components)
    kept = {key: schema[key] for key in KEPT_KEYWORDS if key in schema}

    if isinstance(schema.get("items"), dict):
        kept["items"] = kept_schema(schema["items"], components)

    if isinstance(schema.get("additionalProperties"), dict):
        kept["additionalProperties"] = kept_schema(schema["additionalProperties"], components)

    if isinstance(schema.get("propertyNames"), dict):
        kept["propertyNames"] = kept_schema(schema["propertyNames"], components)

    return kept


def parameter_schema(parameter: dict, components: dict) -> dict:
    schema = resolve(parameter["schema"], components)
    kept = kept_schema(schema, components)
    description = parameter.get("description") or schema.get("description")

    if description:
        kept["description"] = description

    return kept


def body_fields(operation: dict, components: dict) -> tuple[dict, list[str]]:
    """A write's JSON body: its fields (as parameters are declared) and the required ones."""
    content = operation.get("requestBody", {}).get("content", {}).get("application/json")

    if content is None:
        return {}, []

    schema = resolve(content["schema"], components)
    fields = {
        field: {"name": field, "schema": value, "description": value.get("description")}
        for field, value in schema.get("properties", {}).items()
    }

    return fields, schema.get("required", [])


def definition(name: str, entry: dict, operation: dict, components: dict, max_items: int) -> dict:
    """The function the model is given for a tool: its allow-listed parameters (and a write's
    body fields) as the route declares them, `limit` capped at the tool's `max_items`."""
    declared = {parameter["name"]: parameter for parameter in operation.get("parameters", [])}
    body, body_required = body_fields(operation, components)
    properties = {}

    for field in entry.get("body", []):
        if field not in body:
            raise ValueError(f"Tool {name}: the body has no field {field}")

        properties[field] = parameter_schema(body[field], components)

        # An optional field of a change: sent only when the user asked to change it.
        if field not in body_required and field not in entry.get("required", []):
            properties[field]["description"] = "Only when the user asked to change it."

    for param in entry["params"]:
        if param not in declared:
            raise ValueError(f"Tool {name}: the route has no parameter {param}")

        properties[param] = parameter_schema(declared[param], components)

    # A list's page size; a write's body field named `limit` (a topic's questions) is its own.
    if "limit" in entry["params"]:
        properties["limit"]["maximum"] = min(
            properties["limit"].get("maximum", max_items), max_items
        )
        properties["limit"]["description"] = f"Number of items to return, up to {max_items}"

    required = [param for param, parameter in declared.items() if parameter.get("required")]
    # The body's required fields, and those an entry requires of a route that doesn't (one
    # setting of a partial update).
    required += [
        field for field in [*body_required, *entry.get("required", [])] if field not in required
    ]
    missing = [param for param in required if param not in properties]

    if missing:
        raise ValueError(f"Tool {name}: required parameters not allowed: {missing}")

    description = entry.get("description") or operation.get("description") or operation["summary"]

    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        },
    }
