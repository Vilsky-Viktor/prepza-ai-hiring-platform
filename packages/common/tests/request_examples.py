"""The smallest valid request a route's models allow, for the access matrix
(`access_matrix.py`): its required query values and a body with its required fields only, from
their JSON schemas (routes left out of the OpenAPI description included). A route whose body
this can't build (a pattern, a validator) gets one from its test."""

from uuid import uuid4

from fastapi.routing import APIRoute
from pydantic import TypeAdapter

STRINGS = {
    "uuid": lambda: str(uuid4()),
    "email": lambda: "matrix@example.com",
    "date": lambda: "2026-01-01",
    "date-time": lambda: "2026-01-01T00:00:00Z",
    "uri": lambda: "https://example.com",
}


def example(schema: dict, components: dict):
    """A value `schema` accepts, as small as it allows."""
    if "$ref" in schema:
        return example(components[schema["$ref"].rsplit("/", 1)[1]], components)

    if "const" in schema:
        return schema["const"]

    if "enum" in schema:
        return schema["enum"][0]

    for key in ("anyOf", "oneOf", "allOf"):
        if key in schema:
            options = [item for item in schema[key] if item.get("type") != "null"]

            return example(options[0], components)

    return by_type(schema, components)


def by_type(schema: dict, components: dict):
    kind = schema.get("type", "object")

    if kind == "object":
        properties = schema.get("properties", {})

        return {name: example(properties[name], components) for name in schema.get("required", [])}

    if kind == "array":
        return [example(schema.get("items", {}), components)] * max(schema.get("minItems", 1), 1)

    if kind == "string":
        return STRINGS.get(schema.get("format"), lambda: "x" * max(schema.get("minLength", 1), 1))()

    if kind in ("integer", "number"):
        return schema.get("minimum", schema.get("exclusiveMinimum", 0) + 1)

    return False


def schema_of(annotation) -> tuple[dict, dict]:
    """The JSON schema of a type, and the definitions its references point to."""
    found = TypeAdapter(annotation).json_schema()

    return found, found.get("$defs", {})


def query(route: APIRoute) -> dict:
    """A value for each required query parameter, by the name it's sent as."""
    found = {}

    for item in route.dependant.query_params:
        if item.field_info.is_required():
            found[item.field_info.alias or item.name] = example(
                *schema_of(item.field_info.annotation)
            )

    return found


def body(route: APIRoute) -> dict:
    """The keyword arguments for httpx: the JSON body, none without one."""
    if route.body_field is None:
        return {}

    return {"json": example(*schema_of(route.body_field.field_info.annotation))}
