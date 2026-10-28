"""Rounds' old public content addresses, kept one release: a request that still reaches rounds
goes to the same route in site, with its query."""

import pytest


@pytest.mark.parametrize(
    ("path", "target"),
    [
        ("/help/faq?country=DE", "/api/site/help/faq?country=DE"),
        ("/help/guide", "/api/site/help/guide"),
        ("/help/pages/candidate", "/api/site/help/pages/candidate"),
        ("/help/guides", "/api/site/help/guides"),
        ("/help/guides/hiring-engineers", "/api/site/help/guides/hiring-engineers"),
        ("/help/legal/terms?version=2026-10-23", "/api/site/help/legal/terms?version=2026-10-23"),
    ],
)
def test_an_old_content_address_sends_the_browser_to_site(client, path, target):
    response = client.get(path, follow_redirects=False)

    # 307 keeps the method.
    assert (response.status_code, response.headers["location"]) == (307, target)
