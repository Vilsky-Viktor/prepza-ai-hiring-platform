from urllib.parse import quote
from uuid import UUID

# JSON schema types and the Python values that match them (a bool isn't an integer here).
TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool}


def problems(arguments: dict, parameters: dict) -> list[str]:
    """What's wrong with the model's arguments for a tool's `parameters` schema; empty when
    nothing is. A null counts as left out, and an empty required text as missing."""
    properties = parameters["properties"]
    given = {name: value for name, value in arguments.items() if value is not None}
    found = [f"unknown argument {name}" for name in given if name not in properties]
    found += [f"{name} is required" for name in parameters["required"] if name not in given]
    # A required text left empty is missing too: the model asks the user for it.
    found += [
        f"{name} is empty: ask the user for it"
        for name in parameters["required"]
        if isinstance(given.get(name), str) and not given[name].strip()
    ]

    for name, value in given.items():
        if name in properties:
            found += [f"{name} {problem}" for problem in value_problems(value, properties[name])]

    return found


def value_problems(value, schema: dict) -> list[str]:
    expected = TYPES.get(schema.get("type"))

    if expected and (
        not isinstance(value, expected) or (expected is int and isinstance(value, bool))
    ):
        return [f"must be of type {schema['type']}"]

    if "enum" in schema and value not in schema["enum"]:
        return [f"must be one of {schema['enum']}"]

    found = []

    if isinstance(value, str):
        if len(value) > schema.get("maxLength", len(value)):
            found.append(f"must be at most {schema['maxLength']} characters")

        if len(value) < schema.get("minLength", 0):
            found.append(f"must be at least {schema['minLength']} characters")

        if schema.get("format") == "uuid" and not is_uuid(value):
            found.append("must be a UUID")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            found.append(f"must be at least {schema['minimum']}")

        if "maximum" in schema and value > schema["maximum"]:
            found.append(f"must be at most {schema['maximum']}")

    return found


def is_uuid(value: str) -> bool:
    try:
        UUID(value)
    except ValueError:
        return False

    return True


def fill_path(path: str, values: dict) -> str:
    """The route's path with its parameters filled in, each escaped as one path segment."""
    for name, value in values.items():
        path = path.replace(f"{{{name}}}", quote(str(value), safe=""))

    return path


def texts_in(value) -> list[str]:
    """Every string in arguments, however deep in lists and objects (keys too)."""
    if isinstance(value, str):
        return [value]

    if isinstance(value, dict):
        return [text for key, item in value.items() for text in [*texts_in(key), *texts_in(item)]]

    if isinstance(value, list):
        return [text for item in value for text in texts_in(item)]

    return []
