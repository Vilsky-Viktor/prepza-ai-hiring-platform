"""The API key the public API's tests call with (the `key` fixture in conftest.py stores it as
COMPANY's) and a call made with it."""

from prepza_common.http.http import bearer

KEY = "pz_test-key"


def call(client, method, path, key=KEY, **kwargs):
    headers = bearer(key) if key else {}

    return client.request(method, path, headers=headers, **kwargs)
