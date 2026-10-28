import re
from urllib.parse import urlsplit

from companies.constants.allowed_domains import LOOPBACK_HOSTS, NOT_A_DOMAIN
from companies.helpers.verification import DOMAIN, registrable_domain

PORT = re.compile(r"^[0-9]{1,5}$")


def normalized(entries: list[str]) -> list[str]:
    """Each entry as it's kept: lowercase, without a scheme or a path (a pasted
    https://jobs.acme.com/careers is jobs.acme.com), each once, in the order given. A
    ValueError (NOT_A_DOMAIN) names the first that isn't a domain, a "*." wildcard over one, or a
    loopback host with an optional port. A public suffix (co.uk, *.github.io) is refused: anyone
    could put a page there."""
    found = []

    for entry in entries:
        kept = normal(entry)

        if kept is None:
            raise ValueError(NOT_A_DOMAIN.format(entry=entry.strip() or '""'))

        if kept not in found:
            found.append(kept)

    return found


def normal(entry: str) -> str | None:
    text = entry.strip().lower()
    parts = urlsplit(text if "://" in text else f"//{text}")
    host, port = split_port(parts.netloc)

    if host in LOOPBACK_HOSTS and port != "":
        return f"{host}:{port}" if port else host

    if port is not None or parts.netloc != host:
        return None

    wildcard = host.startswith("*.")
    name = host.removeprefix("*.")

    if not DOMAIN.match(name) or registrable_domain(name) is None:
        return None

    return f"*.{name}" if wildcard else name


def split_port(netloc: str) -> tuple[str, str | None]:
    """The host and the port of "host:port" ("[::1]:3000" too); the port None without one, or ""
    when it isn't a number (refused)."""
    host, colon, port = netloc.rpartition(":")

    if not colon or host.endswith(":") or (netloc.startswith("[") and not host.endswith("]")):
        return netloc, None

    return host, port if PORT.match(port) and 0 < int(port) < 65536 else ""


def is_loopback(entry: str) -> bool:
    return split_port(entry)[0] in LOOPBACK_HOSTS


def sources(domains: list[str], allow_localhost: bool) -> list[str]:
    """The Content-Security-Policy sources the domains make (for frame-ancestors): a site without
    a scheme, which matches only the framed page's own (HTTPS in production, so never an HTTP
    page); HTTP and HTTPS on the developer's own computer."""
    found = [entry for entry in domains if not is_loopback(entry)]
    loopback = [entry for entry in domains if is_loopback(entry)]

    if allow_localhost:
        loopback = [f"{host}:*" for host in LOOPBACK_HOSTS]

    for entry in loopback:
        port = "" if ":" in entry.removeprefix("[::1]") else ":*"
        found += [f"http://{entry}{port}", f"https://{entry}{port}"]

    return found


def allows(
    domains: list[str], allow_localhost: bool, url: str | None, https_only: bool = True
) -> bool:
    """Whether a page at `url` (an address or an origin) is on an allowed domain: HTTPS (any
    scheme without `https_only`) on a domain the list names, or on a subdomain a "*." entry
    names; HTTP or HTTPS on the developer's own computer when it's allowed (the switch, or its
    entry, with its port)."""
    parts = urlsplit((url or "").strip().lower())

    if parts.scheme not in ("http", "https") or not parts.hostname:
        return False

    host, port = split_port(parts.netloc.rpartition("@")[2])

    if host in LOOPBACK_HOSTS:
        return allow_localhost or host in domains or f"{host}:{port}" in domains

    return (
        (parts.scheme == "https" or not https_only)
        and port is None
        and any(
            host == entry or (entry.startswith("*.") and host.endswith(entry[1:]))
            for entry in domains
        )
    )


def frame_sources(
    domains: list[str], allow_localhost: bool, origin: str | None, referrer: str | None
) -> list[str]:
    """Who may frame an embedded interview (sources): none when the page the frame says it's on
    (`origin`, which the script passes) or the page the browser says it came from (`referrer`)
    is given and isn't on an allowed domain; the allowed domains otherwise. The browser enforces
    the sources, and their scheme, whatever a page claims; the claims only refuse sooner."""
    for claimed in (origin, referrer):
        if claimed and not allows(domains, allow_localhost, claimed, https_only=False):
            return []

    return sources(domains, allow_localhost)
