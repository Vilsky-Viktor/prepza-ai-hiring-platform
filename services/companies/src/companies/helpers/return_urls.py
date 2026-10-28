from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def on_domain(url: str, domain: str | None) -> bool:
    """Whether `url` is an https address on the company's website domain or a subdomain of it,
    so a return link can't send candidates to someone else's site."""
    if not domain:
        return False

    parts = urlsplit(url)
    host = (parts.hostname or "").lower()

    return parts.scheme == "https" and (host == domain or host.endswith(f".{domain}"))


def with_invite(url: str, invite_id) -> str:
    """The return address with the invite's id, so the company's platform knows who came back."""
    parts = urlsplit(url)
    query = urlencode([*parse_qsl(parts.query), ("prepza_invite", str(invite_id))])

    return urlunsplit(parts._replace(query=query))
