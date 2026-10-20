import ipaddress
import socket
from urllib.parse import urlsplit

import httpx


def public_address(url: str) -> str | None:
    """The address to connect to, when the URL is HTTPS to a host whose every address is on the
    public internet, so a request to an address someone gave (a web hook, an AI app's metadata)
    can't reach prepza's own services or the cloud's metadata server; None otherwise. The request
    connects to this very address (`pinned`), so a second lookup that answers differently (DNS
    rebinding) can't lead it elsewhere. A lookup that fails raises socket.gaierror: it may work
    on a retry. Blocking: run it in a thread."""
    parts = urlsplit(url)

    if parts.scheme != "https" or not parts.hostname:
        return None

    try:
        found = socket.getaddrinfo(parts.hostname, parts.port or 443, proto=socket.IPPROTO_TCP)
    except UnicodeError:
        return None

    addresses = [item[4][0] for item in found]

    if not all(ipaddress.ip_address(address).is_global for address in addresses):
        return None

    return addresses[0]


def pinned(url: str, address: str) -> tuple[httpx.URL, dict[str, str], dict[str, str]]:
    """What an httpx request to `url` at the checked `address` takes: the URL with that address,
    the host's name in the Host header, and the extension that keeps TLS (SNI and the
    certificate check) on the host's name. Use a client keeping no connections, or one opened for
    a host would be reused for another host at the same address."""
    target = httpx.URL(url)

    return (
        target.copy_with(host=address),
        {"Host": target.netloc.decode()},
        {"sni_hostname": target.raw_host.decode()},
    )
