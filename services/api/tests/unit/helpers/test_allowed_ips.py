import pytest

from api.helpers.allowed_ips import allows, normalized


def test_entries_are_kept_in_their_shortest_form_each_once():
    entries = [" 203.0.113.7 ", "203.0.113.7/32", "2001:DB8::1", "10.0.0.0/8", "2001:db8::/32"]

    assert normalized(entries) == ["203.0.113.7", "2001:db8::1", "10.0.0.0/8", "2001:db8::/32"]


@pytest.mark.parametrize("entry", ["", "example.com", "203.0.113.300", "10.0.0.5/24", "::1/129"])
def test_an_entry_that_isnt_an_address_or_a_clean_range_is_refused(entry):
    with pytest.raises(ValueError):
        normalized([entry])


@pytest.mark.parametrize(
    ("allowed", "address", "expected"),
    [
        ([], "198.51.100.1", True),
        ([], None, True),
        (["203.0.113.7"], "203.0.113.7", True),
        (["203.0.113.7"], "203.0.113.8", False),
        (["203.0.113.0/24"], "203.0.113.200", True),
        (["203.0.113.0/24"], "203.0.114.1", False),
        (["2001:db8::/32"], "2001:db8:abcd::5", True),
        (["2001:db8::/32"], "2001:db9::5", False),
        (["203.0.113.7"], "::ffff:203.0.113.7", True),
        (["203.0.113.7"], None, False),
        (["203.0.113.7"], "unknown", False),
    ],
)
def test_a_key_with_addresses_allows_only_those(allowed, address, expected):
    assert allows(allowed, address) is expected
