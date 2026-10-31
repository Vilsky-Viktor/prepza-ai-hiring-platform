import ipaddress

from fastapi import Request

# An IPv6 visitor is one network of this size: a home or office gets a whole /64, and could
# take a fresh address from it for every request.
IPV6_PREFIX = 64


def client_ip(request: Request) -> str:
    """The visitor's address. Google's load balancer appends "<client>,<load balancer>" to
    X-Forwarded-For, after whatever the visitor sent, so the client is the second entry from
    the end; anything earlier can be made up. Without that (locally), the connection's address.
    """
    entries = [part.strip() for part in request.headers.get("x-forwarded-for", "").split(",")]

    if len(entries) >= 2 and entries[-2]:
        return entries[-2]

    return request.client.host if request.client else "unknown"


def limit_address(request: Request) -> str:
    """The visitor's address as per-address limits count it: an IPv4 address as it is, an IPv6
    one as its /64 network, so changing the last part of the address doesn't give a fresh count."""
    address = client_ip(request)

    try:
        parsed = ipaddress.ip_address(address)
    except ValueError:
        return address

    if parsed.version == 6:
        return str(ipaddress.ip_network(f"{parsed}/{IPV6_PREFIX}", strict=False))

    return address
