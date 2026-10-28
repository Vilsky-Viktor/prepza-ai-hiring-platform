import uuid

import pytest

from companies.helpers.return_urls import on_domain, with_invite


@pytest.mark.parametrize(
    "url, allowed",
    [
        ("https://acme.com/hiring/next", True),
        ("https://careers.acme.com/step/3?x=1", True),
        ("http://acme.com/next", False),
        ("https://evil.com/acme.com", False),
        ("https://acme.com.evil.com/", False),
        ("https://notacme.com/", False),
        ("javascript:alert(1)", False),
    ],
)
def test_a_return_address_stays_on_the_companys_website(url, allowed):
    assert on_domain(url, "acme.com") is allowed


def test_no_website_no_return_address():
    assert on_domain("https://acme.com/next", None) is False


def test_the_return_address_names_the_invite():
    invite_id = uuid.uuid4()

    assert with_invite("https://acme.com/next?step=3", invite_id) == (
        f"https://acme.com/next?step=3&prepza_invite={invite_id}"
    )
