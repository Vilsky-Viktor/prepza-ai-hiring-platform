def trim(value, fields: frozenset[str] | None, max_items: int, max_length: int):
    """What the model reads of a tool's data: only allow-listed keys (at every level), no nulls,
    lists of at most `max_items` (a longer one becomes {"items", "shown", "more"}) and strings of
    at most `max_length` characters."""
    if isinstance(value, dict):
        return {
            key: trim(item, fields, max_items, max_length)
            for key, item in value.items()
            if item is not None and (fields is None or key in fields)
        }

    if isinstance(value, list):
        items = [trim(item, fields, max_items, max_length) for item in value[:max_items]]

        if len(value) <= max_items:
            return items

        return {"items": items, "shown": len(items), "more": True}

    if isinstance(value, str) and len(value) > max_length:
        return value[:max_length] + "…"

    return value
