import socket

import pytest

from prepza_common import public_urls
from prepza_common.public_urls import pinned, public_address


@pytest.mark.parametrize(
    ("url", "addresses", "address"),
    [
        ("https://example.com/hook", ["93.184.216.34", "2606:2800::1"], "93.184.216.34"),
        ("http://example.com/hook", ["93.184.216.34"], None),
        ("https://localhost/hook", ["127.0.0.1"], None),
        ("https://metadata/hook", ["169.254.169.254"], None),
        ("https://intranet/hook", ["10.0.0.5"], None),
        ("https://split/hook", ["93.184.216.34", "192.168.1.2"], None),
    ],
)
def test_only_https_to_the_public_internet_and_the_address_checked(
    monkeypatch, url, addresses, address
):
    def resolve(host, port, proto=0):
        return [(socket.AF_INET, 1, 6, "", (address, port)) for address in addresses]

    monkeypatch.setattr(public_urls.socket, "getaddrinfo", resolve)

    assert public_address(url) == address


def test_a_failed_lookup_raises_so_the_request_can_be_retried(monkeypatch):
    def resolve(host, port, proto=0):
        raise socket.gaierror

    monkeypatch.setattr(public_urls.socket, "getaddrinfo", resolve)

    with pytest.raises(socket.gaierror):
        public_address("https://unknown/hook")


def test_a_pinned_request_goes_to_the_address_with_the_hosts_name():
    url, headers, extensions = pinned("https://hooks.example.com:8443/a?b=1", "93.184.216.34")

    assert str(url) == "https://93.184.216.34:8443/a?b=1"
    assert headers == {"Host": "hooks.example.com:8443"}
    assert extensions == {"sni_hostname": "hooks.example.com"}
