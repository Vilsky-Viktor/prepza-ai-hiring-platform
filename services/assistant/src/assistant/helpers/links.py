from assistant.constants.tool_calls import TOKEN_LINKS


def with_links(data, site_url: str):
    """A tool's data with each link's code replaced by the full link on `site_url`, so the
    model never reads a bare code (a turned-off link's null stays null)."""
    if not isinstance(data, dict):
        return data

    data = dict(data)
    site = site_url.rstrip("/")

    for token, (url, path) in TOKEN_LINKS.items():
        if token in data:
            code = data.pop(token)
            data[url] = f"{site}{path.format(code)}" if code else None

    return data
