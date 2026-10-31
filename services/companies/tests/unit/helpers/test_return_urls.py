import uuid

import pytest

from companies.helpers.return_urls import is_return_url, with_invite


def test_the_return_address_names_the_invite():
    invite_id = uuid.uuid4()

    assert with_invite("https://acme.com/next?step=3", invite_id) == (
        f"https://acme.com/next?step=3&testee_invite={invite_id}"
    )


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://jobs.acme.com/done?step=2", True),
        ("https://anywhere.example.org", True),
        ("http://localhost:3000/done", True),
        ("http://127.0.0.1:8080/done", True),
        ("http://jobs.acme.com/done", False),
        ("javascript:alert(1)", False),
        ("data:text/html,hi", False),
        ("https:/no-host", False),
        ("https://[bad", False),
        ("", False),
    ],
)
def test_a_return_address_is_https_or_http_on_localhost(url, expected):
    assert is_return_url(url) is expected
