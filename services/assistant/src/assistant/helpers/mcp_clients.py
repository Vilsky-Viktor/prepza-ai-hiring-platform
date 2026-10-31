from urllib.parse import urlparse

from mcp.shared.auth import OAuthClientInformationFull
from pydantic import ValidationError

from assistant.constants.mcp import (
    KNOWN_CLIENTS,
    KNOWN_SCHEMES,
    LOCAL_APP,
    LOOPBACK_HOSTS,
    MAX_CLIENT_NAME_LENGTH,
    METADATA_DOCUMENT_AUTH,
    REFUSED_REDIRECT_SCHEMES,
)


def describe_client(reported_name: str | None, redirect_uri: str) -> tuple[str, str, bool]:
    """What the consent page names an app by: (its name, the site it returns to, whether testee
    knows it). A known site, or a known desktop app's own scheme, names the app, whatever it
    calls itself; an app on the user's own computer is named as it says; any other is unknown,
    and its name is only what it says. Only an https address is a known site
    (javascript://claude.ai/ isn't Claude); names are cut to what a connection keeps."""
    url = urlparse(redirect_uri)
    host = (url.hostname or "").lower()
    reported = (reported_name or "").strip()[:MAX_CLIENT_NAME_LENGTH]

    if url.scheme == "https" and host in KNOWN_CLIENTS:
        return KNOWN_CLIENTS[host], host, True

    # A desktop app's own scheme: the site it returns to is that app.
    if url.scheme in KNOWN_SCHEMES:
        return KNOWN_SCHEMES[url.scheme], f"{url.scheme}://", True

    if url.scheme in ("http", "https") and host in LOOPBACK_HOSTS:
        return reported or LOCAL_APP, host, True

    return reported or host[:MAX_CLIENT_NAME_LENGTH], host, False


def refused_redirect(redirect_uri: str) -> bool:
    """A return address that would run or read something in the browser instead of opening an
    app (constants/mcp.py REFUSED_REDIRECT_SCHEMES)."""
    return urlparse(redirect_uri).scheme.lower() in REFUSED_REDIRECT_SCHEMES


def is_document_id(client_id: str) -> bool:
    """A client_id that is the address of the app's Client ID Metadata Document: HTTPS, with a
    path, without a fragment."""
    url = urlparse(client_id)

    return (
        url.scheme == "https"
        and bool(url.hostname)
        and url.path not in ("", "/")
        and not (url.fragment)
    )


def document_client(client_id: str, document: dict) -> dict | None:
    """What a connection keeps of an app's metadata document, as the MCP SDK's
    OAuthClientInformationFull: only one that names itself by this very address, has no secret,
    and returns to addresses that open an app. None for any other."""
    method = document.get("token_endpoint_auth_method", METADATA_DOCUMENT_AUTH)
    redirects = document.get("redirect_uris")

    if document.get("client_id") != client_id or method != METADATA_DOCUMENT_AUTH:
        return None

    if not isinstance(redirects, list) or not redirects:
        return None

    if any(not isinstance(uri, str) or refused_redirect(uri) for uri in redirects):
        return None

    kept = {key: value for key, value in document.items() if key != "client_secret"}

    try:
        client = OAuthClientInformationFull.model_validate(
            {**kept, "token_endpoint_auth_method": METADATA_DOCUMENT_AUTH}
        )
    except ValidationError:
        return None

    return client.model_dump(mode="json", exclude_none=True)


def same_loopback(registered: list[str], given: str) -> bool:
    """A return address on the user's own computer that matches a registered one but for its
    port: an app there listens on whatever port is free (RFC 8252, 7.3)."""
    url = urlparse(given)

    if url.scheme != "http" or url.hostname not in LOOPBACK_HOSTS:
        return False

    def unported(found) -> tuple:
        return (found.scheme, found.hostname, found.path, found.query)

    return any(unported(urlparse(uri)) == unported(url) for uri in registered)
