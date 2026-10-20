import httpx

from app.helpers.arguments import fill_path
from app.integrations import services
from app.models.tools import Tool


async def subject_of(tool: Tool, arguments: dict, token: str, language: str) -> dict | None:
    """What the action is about, as the user may see it now (a company, an interview), read
    with their token; raises LookupError when it's not theirs or is gone."""
    entry = tool.subject

    if entry is None:
        return None

    path = fill_path(entry["path"], arguments)
    query = {name: arguments[name] for name in entry.get("query", []) if name in arguments}

    try:
        response = await services.get(entry["service"], path, query, token, language)
    except httpx.HTTPError:
        return None

    if not response.is_success:
        raise LookupError

    data = response.json()

    if isinstance(data, list):
        wanted = str(arguments[entry["match"]])
        data = next((item for item in data if str(item.get("id")) == wanted), None)

        if data is None:
            raise LookupError

    return data if isinstance(data, dict) else None


async def already_done(tool: Tool, arguments: dict, token: str, language: str) -> bool:
    """Whether the action would change nothing (`done_when`), read with the user's token; False
    when it can't be read: the service decides then."""
    entry = tool.done_when

    if entry is None:
        return False

    try:
        response = await services.get(
            entry["service"], fill_path(entry["path"], arguments), {}, token, language
        )
    except httpx.HTTPError:
        return False

    found = response.json() if response.is_success else {}

    return isinstance(found, dict) and found.get(entry["field"]) == entry["value"]
