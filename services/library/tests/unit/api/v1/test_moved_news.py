"""Library's old news addresses, kept one release: a request that still reaches library goes to
the same route in site, with its method, body and query."""

import pytest


@pytest.mark.parametrize(
    ("method", "path", "target"),
    [
        ("GET", "/news?offset=0&limit=10", "/api/site/news?offset=0&limit=10"),
        ("GET", "/superadmin/news?limit=100", "/api/site/superadmin/news?limit=100"),
        ("POST", "/superadmin/news", "/api/site/superadmin/news"),
        ("PUT", "/superadmin/news/n1", "/api/site/superadmin/news/n1"),
        ("DELETE", "/superadmin/news/n1", "/api/site/superadmin/news/n1"),
    ],
)
def test_an_old_news_address_sends_the_browser_to_site(client, method, path, target):
    response = client.request(method, path, json={"a": 1}, follow_redirects=False)

    # 307 keeps the method and the body.
    assert (response.status_code, response.headers["location"]) == (307, target)
