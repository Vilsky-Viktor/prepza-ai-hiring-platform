import pytest

from companies.helpers.allowed_domains import allows, normalized, sources


def test_entries_are_kept_lowercase_without_scheme_or_path_each_once():
    entries = [" https://Jobs.Acme.com/careers ", "jobs.acme.com", "*.acme.com", "localhost:3000"]

    assert normalized(entries) == ["jobs.acme.com", "*.acme.com", "localhost:3000"]


@pytest.mark.parametrize(
    "entry",
    [
        "",
        "acme",
        "co.uk",
        "*.github.io",
        "*.com",
        "acme.com:8443",
        "localhost:abc",
        "a b.com",
        "javascript:alert(1)",
        "user@acme.com",
        "203.0.113.7",
    ],
)
def test_an_entry_that_isnt_a_domain_is_refused(entry):
    with pytest.raises(ValueError):
        normalized([entry])


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://jobs.acme.com/apply?x=1", True),
        ("https://acme.com", False),
        ("https://eu.careers.acme.com", True),
        ("https://careers.acme.com", False),
        # The frame's sources hold the page to HTTPS; the claim only refuses sooner.
        ("http://jobs.acme.com", True),
        ("https://jobs.acme.com:8443", False),
        ("https://jobs.acme.com.evil.com", False),
        ("https://evilacme.com", False),
        ("https://jobs.acme.com@evil.com", False),
        ("javascript:alert(1)", False),
        (None, False),
        ("http://localhost:3000/x", False),
    ],
)
def test_a_page_must_be_on_an_allowed_domain(url, expected):
    assert allows(["jobs.acme.com", "*.careers.acme.com"], False, url) is expected


def test_a_wildcard_allows_subdomains_but_not_the_domain_itself():
    assert allows(["*.acme.com"], False, "https://jobs.acme.com")
    assert not allows(["*.acme.com"], False, "https://acme.com")


def test_localhost_is_refused_until_the_company_opts_in():
    page = "http://localhost:3000"

    assert not allows(["acme.com"], False, page)
    assert allows(["acme.com"], True, page)
    assert allows(["localhost:3000"], False, page)
    assert not allows(["localhost:3000"], False, "http://localhost:4000")
    assert allows(["localhost"], False, "http://localhost:4000")
    assert allows([], True, "http://127.0.0.1:8080")
    assert allows([], True, "http://[::1]:8080")


def test_the_domains_make_frame_ancestors_sources():
    assert sources(["acme.com", "*.acme.com", "localhost:3000"], False) == [
        "acme.com",
        "*.acme.com",
        "http://localhost:3000",
        "https://localhost:3000",
    ]
    assert sources(["[::1]"], False) == ["http://[::1]:*", "https://[::1]:*"]
    assert sources(["acme.com", "localhost:3000"], True) == [
        "acme.com",
        "http://localhost:*",
        "https://localhost:*",
        "http://127.0.0.1:*",
        "https://127.0.0.1:*",
        "http://[::1]:*",
        "https://[::1]:*",
    ]
    assert sources([], False) == []
