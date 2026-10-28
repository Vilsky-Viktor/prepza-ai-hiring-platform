import ipaddress


def normalized(entries: list[str]) -> list[str]:
    """Each IPv4 or IPv6 address or CIDR range as it's kept: a single address without its
    prefix, a range in its shortest form, each once, in the order given. A ValueError names the
    first entry that isn't one, or a range with bits set after its prefix (10.0.0.5/24), which
    likely isn't what was meant."""
    found = []

    for entry in entries:
        text = entry.strip()

        try:
            network = ipaddress.ip_network(text)
        except ValueError:
            raise ValueError(
                f"{text or 'An empty entry'} isn't an IP address or a range like 203.0.113.0/24"
            ) from None

        kept = network.with_prefixlen

        if network.prefixlen == network.max_prefixlen:
            kept = str(network.network_address)

        if kept not in found:
            found.append(kept)

    return found


def allows(allowed: list[str], address: str | None) -> bool:
    """Whether a key with these allowed addresses may be used from `address`: any address when
    the list is empty; otherwise only one inside an entry. An IPv4 address an IPv6 connection
    carries (::ffff:203.0.113.7) counts as that IPv4 address."""
    if not allowed:
        return True

    try:
        parsed = ipaddress.ip_address(address or "")
    except ValueError:
        return False

    if parsed.version == 6 and parsed.ipv4_mapped is not None:
        parsed = parsed.ipv4_mapped

    return any(parsed in ipaddress.ip_network(entry) for entry in allowed)
