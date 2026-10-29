from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from companies.constants.return_urls import LOCAL_HOSTS


def with_invite(url: str, invite_id) -> str:
    """The return address with the invite's id, so the company's platform knows who came back."""
    parts = urlsplit(url)
    query = urlencode([*parse_qsl(parts.query), ("prepza_invite", str(invite_id))])

    return urlunsplit(parts._replace(query=query))


def is_return_url(url: str) -> bool:
    """Whether the candidate may be taken to `url` once they've finished: https to any host, or
    http to the developer's own computer (LOCAL_HOSTS)."""
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return False

    if not parts.hostname:
        return False

    return parts.scheme == "https" or (parts.scheme == "http" and parts.hostname in LOCAL_HOSTS)
