from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def with_invite(url: str, invite_id) -> str:
    """The return address with the invite's id, so the company's platform knows who came back."""
    parts = urlsplit(url)
    query = urlencode([*parse_qsl(parts.query), ("prepza_invite", str(invite_id))])

    return urlunsplit(parts._replace(query=query))
