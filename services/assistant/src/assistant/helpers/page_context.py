import json

from assistant.prompts.assistant import PAGE_ID_NAMES, PAGE_KEY, PAGE_PATH


def describe_page(page: dict) -> str:
    """The page a message was asked on, for the model: its guide's key, its path with the query
    (quoted: it's the client's text) and the ids it's about, each named."""
    text = PAGE_KEY.format(key=page["key"]) if page.get("key") else ""
    text += PAGE_PATH.format(path=json.dumps(page["path"]))
    ids = [
        f"{name} with id {page[field]}" for field, name in PAGE_ID_NAMES.items() if page.get(field)
    ]

    if ids:
        text += f", about {' and '.join(ids)}"

    return text
