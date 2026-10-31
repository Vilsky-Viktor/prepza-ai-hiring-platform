import json
from functools import cache
from pathlib import Path

from testee_common.config.constants import MAX_UPDATES

from assistant.constants.tool_calls import DEFAULT_MAX_ITEMS, MAX_STRING_LENGTH, SERVICE_URLS
from assistant.constants.tools import TOOLS
from assistant.constants.updates import GET_UPDATES, GET_UPDATES_DEFINITION, UPDATES_PATH
from assistant.helpers.tool_schema import check_route, definition
from assistant.models.tools import Tool

# Each service's OpenAPI description, written by scripts/assistant-openapi.sh.
SNAPSHOTS = Path(__file__).resolve().parents[1] / "openapi"


@cache
def snapshot(service: str) -> dict:
    return json.loads((SNAPSHOTS / f"{service}.json").read_text())


def build(name: str, entry: dict) -> Tool:
    """A tool from its allow-list entry; raises when the entry is refused or its route, or one
    of its parameters, isn't in the service's snapshot."""
    check_route(name, entry)

    if entry["service"] not in SERVICE_URLS:
        raise ValueError(f"Tool {name}: unknown service {entry['service']}")

    spec = snapshot(entry["service"])
    method = entry["method"]
    operation = spec["paths"].get(entry["path"], {}).get(method.lower())

    if operation is None:
        raise ValueError(f"Tool {name}: {entry['service']} has no {method} {entry['path']}")

    max_items = entry.get("max_items", DEFAULT_MAX_ITEMS)
    schemas = spec.get("components", {}).get("schemas", {})
    function = definition(name, entry, operation, schemas, max_items)
    located = {parameter["name"]: parameter["in"] for parameter in operation.get("parameters", [])}
    fields = entry.get("fields")

    return Tool(
        name=name,
        service=entry["service"],
        method=method,
        path=entry["path"],
        path_params=tuple(param for param in entry["params"] if located[param] == "path"),
        query_params=tuple(param for param in entry["params"] if located[param] == "query"),
        definition=function,
        fields=frozenset(fields) if fields is not None else None,
        max_items=max_items,
        max_length=entry.get("max_length", MAX_STRING_LENGTH),
        render=entry.get("render"),
        link=entry.get("link"),
        body_params=tuple(entry.get("body", [])),
        confirm=entry.get("confirm", False),
        destructive=entry.get("destructive", False),
        preview=tuple(entry.get("preview", entry.get("body", []))),
        subject=entry.get("subject"),
        credits=entry.get("credits", False),
        done_when=entry.get("done_when"),
        result_label=entry.get("result_label"),
    )


def updates_tool() -> Tool:
    """get_updates, a read of the notifications service's internal feed: services/updates.py
    carries it out, never the generic call of a user-facing route."""
    return Tool(
        name=GET_UPDATES,
        service="notifications",
        method="GET",
        path=UPDATES_PATH,
        path_params=(),
        query_params=(),
        definition=GET_UPDATES_DEFINITION,
        fields=None,
        max_items=MAX_UPDATES,
        max_length=MAX_STRING_LENGTH,
        render=None,
        link=None,
    )


@cache
def tools() -> dict[str, Tool]:
    """Every tool, built once; the service doesn't start when one can't be."""
    built = {name: build(name, entry) for name, entry in TOOLS.items()}

    return {**built, GET_UPDATES: updates_tool()}
