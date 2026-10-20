from mcp.server.auth.handlers.metadata import MetadataHandler
from mcp.server.auth.middleware.client_auth import AuthenticationError, ClientAuthenticator
from mcp.server.auth.routes import (
    AUTHORIZATION_PATH,
    REGISTRATION_PATH,
    REVOCATION_PATH,
    build_metadata,
    cors_middleware,
    create_auth_routes,
    create_protected_resource_routes,
)
from mcp.server.auth.settings import ClientRegistrationOptions, RevocationOptions
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from app.constants.mcp import (
    AUTH_METHODS,
    AUTHORIZATION_METADATA_PATH,
    MCP_SCOPE,
    ROOT_RESOURCE_METADATA_PATH,
)
from app.helpers.authorize_guard import GuardAuthorize
from app.helpers.oauth import auth_settings
from app.services.oauth_limits import Limited
from app.services.oauth_provider import Provider


async def revoke(request: Request) -> Response:
    """An app revoking its access or refresh token (RFC 7009): the connection goes. Answered
    here rather than by the SDK's handler, which requires a client_secret field that apps
    registered without a secret don't send. An unknown token is a 200 too."""
    provider = Provider()

    try:
        client = await ClientAuthenticator(provider).authenticate_request(request)
    except AuthenticationError as error:
        body = {"error": "unauthorized_client", "error_description": error.message}

        return JSONResponse(body, status_code=401)

    token = (await request.form()).get("token")

    if not isinstance(token, str) or not token:
        return JSONResponse({"error": "invalid_request"}, status_code=400)

    found = await provider.load_access_token(token) or await provider.load_refresh_token(
        client, token
    )

    if found is not None and found.client_id == client.client_id:
        await provider.revoke_token(found)

    return Response(status_code=200, headers={"Cache-Control": "no-store"})


def routes() -> list[Route]:
    """prepza as the authorization server of AI apps, at the site's root (the MCP SDK's
    handlers): its metadata, /authorize (to the consent page), /token, /register and /revoke; and
    the MCP endpoint's resource metadata, which names it."""
    urls = auth_settings()
    issuer = urls.issuer_url
    registration = ClientRegistrationOptions(
        enabled=True, valid_scopes=[MCP_SCOPE], default_scopes=[MCP_SCOPE]
    )
    revocation = RevocationOptions(enabled=True)
    metadata = build_metadata(issuer, None, registration, revocation)
    metadata.token_endpoint_auth_methods_supported = AUTH_METHODS
    metadata.revocation_endpoint_auth_methods_supported = AUTH_METHODS
    # Every answer to /authorize names the issuer (services/connections.py, RFC 9207).
    metadata.authorization_response_iss_parameter_supported = True
    found = []

    for route in create_auth_routes(Provider(), issuer, None, registration, revocation):
        if route.path == AUTHORIZATION_METADATA_PATH:
            handler = cors_middleware(MetadataHandler(metadata).handle, ["GET", "OPTIONS"])
            route = Route(route.path, endpoint=handler, methods=["GET", "OPTIONS"])
        elif route.path == REGISTRATION_PATH:
            limited = Limited(
                route.app,
                "register",
                "invalid_client_metadata",
                "REGISTRATIONS_PER_IP_HOUR",
                "REGISTRATIONS_PER_DAY",
            )
            route = Route(route.path, endpoint=limited, methods=["POST", "OPTIONS"])
        elif route.path == AUTHORIZATION_PATH:
            limited = Limited(
                route.app, "authorize", "invalid_request", "AUTHORIZATIONS_PER_IP_HOUR"
            )
            route = Route(route.path, endpoint=GuardAuthorize(limited), methods=["GET", "POST"])
        elif route.path == REVOCATION_PATH:
            handler = cors_middleware(revoke, ["POST", "OPTIONS"])
            route = Route(route.path, endpoint=handler, methods=["POST", "OPTIONS"])

        found.append(route)

    resource = create_protected_resource_routes(
        urls.resource_server_url, [issuer], scopes_supported=[MCP_SCOPE], resource_name="prepza"
    )
    root = Route(ROOT_RESOURCE_METADATA_PATH, endpoint=resource[0].app, methods=["GET", "OPTIONS"])

    return [*found, *resource, root]
