"""The gateway's nginx.conf keeps nginx's inheritance trap closed: a block with any `add_header`
or `proxy_set_header` of its own inherits none of the server's, so it must repeat them."""

import re
from pathlib import Path

CONF = Path(__file__).resolve().parents[2] / "gateway" / "nginx.conf"

# The site's pages say who may frame them in their own Content-Security-Policy.
LEFT_OUT = {"/": {"X-Frame-Options"}}


def blocks(text: str) -> tuple[str, dict[str, str]]:
    """The server block's own lines and each location's body, by its match."""
    server = text[text.index("server {") :]
    locations = {}
    own = []
    depth = 0
    current = None

    for line in server.splitlines()[1:]:
        stripped = line.strip()
        opened = re.match(r"location\s+(.+?)\s*\{$", stripped)

        if opened and depth == 0:
            current = opened.group(1)
            locations[current] = ""
            depth = 1

            continue

        if current is None:
            own.append(stripped)

            continue

        depth += stripped.count("{") - stripped.count("}")

        if depth == 0:
            current = None
        else:
            locations[current] += stripped + "\n"

    return "\n".join(own), locations


def names(body: str, directive: str) -> set[str]:
    return set(re.findall(rf"^{directive}\s+(\S+)", body, re.MULTILINE))


def test_a_block_with_its_own_headers_repeats_the_servers():
    server, locations = blocks(CONF.read_text())
    expected = names(server, "add_header")

    assert expected

    for match, body in locations.items():
        own = names(body, "add_header")

        if own:
            assert own == expected - LEFT_OUT.get(match, set()), match


def test_a_block_with_its_own_proxy_headers_repeats_the_servers():
    server, locations = blocks(CONF.read_text())
    expected = names(server, "proxy_set_header")

    assert expected

    for match, body in locations.items():
        own = names(body, "proxy_set_header")

        if own:
            assert expected <= own, match


def test_every_header_is_sent_on_errors_too():
    for line in CONF.read_text().splitlines():
        if line.strip().startswith("add_header"):
            assert line.rstrip().endswith("always;"), line
