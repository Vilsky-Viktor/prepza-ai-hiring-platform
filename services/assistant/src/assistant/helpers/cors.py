from urllib.parse import urlsplit

from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp

from assistant.config import settings
from assistant.constants.mcp import BROWSER_APP_ORIGINS


def browser_origins() -> list[str]:
    """The pages that may call the MCP endpoint and the OAuth endpoints from a browser: the
    site's own and the browser-based apps we know (BROWSER_APP_ORIGINS). AI apps call from their
    servers or the user's computer, where no browser asks."""
    site = urlsplit(settings.site_url)

    return [f"{site.scheme}://{site.netloc}", *BROWSER_APP_ORIGINS]


def browser_cors(
    app: ASGIApp, methods: list[str], headers: list[str], expose: list[str] | None = None
) -> CORSMiddleware:
    """`app` answering those pages only, never with credentials (access rides on the bearer
    header, never a cookie)."""
    return CORSMiddleware(
        app,
        allow_origins=browser_origins(),
        allow_methods=methods,
        allow_headers=headers,
        expose_headers=expose or [],
    )


def narrowed(app: ASGIApp) -> ASGIApp:
    """An MCP SDK route's app with its any-origin CORS narrowed to browser_origins, its methods
    and headers kept; any other app as it is."""
    if not isinstance(app, CORSMiddleware):
        return app

    return browser_cors(app.app, list(app.allow_methods), list(app.allow_headers))
