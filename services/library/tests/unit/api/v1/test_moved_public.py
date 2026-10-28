"""Library's old public account addresses, kept one release: a request that still reaches
library goes to the same route in accounts, with its method, body and query."""

import pytest


@pytest.mark.parametrize(
    ("method", "path", "target"),
    [
        ("GET", "/me", "/api/accounts/me"),
        ("DELETE", "/me", "/api/accounts/me"),
        ("GET", "/me/export", "/api/accounts/me/export"),
        ("PUT", "/me/settings", "/api/accounts/me/settings"),
        ("PUT", "/me/email-preferences", "/api/accounts/me/email-preferences"),
        ("POST", "/superadmin/emails/lookup", "/api/accounts/superadmin/emails/lookup"),
        ("GET", "/superadmin/stats?period=2026", "/api/accounts/superadmin/stats?period=2026"),
    ],
)
def test_an_old_account_address_sends_the_browser_to_accounts(client, method, path, target):
    response = client.request(method, path, json={"a": 1}, follow_redirects=False)

    # 307 keeps the method and the body.
    assert (response.status_code, response.headers["location"]) == (307, target)
