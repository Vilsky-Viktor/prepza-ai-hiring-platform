from mcp.server.auth.handlers.metadata import MetadataHandler
from mcp.server.auth.handlers.token import TokenHandler
from mcp.server.auth.middleware.client_auth import AuthenticationError, ClientAuthenticator
from mcp.server.auth.routes import (
    AUTHORIZATION_PATH,
    REGISTRATION_PATH,
    REVOCATION_PATH,
    TOKEN_PATH,
    build_metadata,
    cors_middleware,
    create_auth_routes,
    create_protected_resource_routes,
)
from mcp.server.auth.settings import ClientRegistrationOptions, RevocationOptions
from mcp.server.transport_security import DEFAULT_MAX_REQUEST_BODY_SIZE, RequestBodyLimitMiddleware
from mcp.shared.inbound import MCP_PROTOCOL_VERSION_HEADER
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route, request_response
from starlette.types import ASGIApp

from app.constants.mcp import (
    AUTH_METHODS,
    AUTHORIZATION_METADATA_PATH,
    MCP_SCOPE,
    MCP_SCOPES,
    OTHER_RESOURCE,
    ROOT_RESOURCE_METADATA_PATH,
)
from app.helpers.authorize_guard import GuardAuthorize
from app.helpers.oauth import auth_settings, other_resource
from app.services.oauth_limits import Limited, token_refusal
from app.services.oauth_provider import Provider


async def revoke(request: Request) -> Response:
    """An app revoking its access or refresh token (RFC 7009): the connection goes. Answered
    here rather than by the SDK's handler, which requires a client_secret field that apps
    registered without a secret don't send. An unknown token is a 200 too. Counted against the
    app's token limit, as /token is."""
    provider = Provider()
    form = await request.form()
    client_id = form.get("client_id")

    if isinstance(client_id, str):
        refused = await token_refusal(request, client_id)

        if refused is not None:
            return refused

    try:
        client = await ClientAuthenticator(provider).authenticate_request(request)
    except AuthenticationError as error:
        body = {"error": "unauthorized_client", "error_description": error.message}

        return JSONResponse(body, status_code=401)

    token = form.get("token")

    if not isinstance(token, str) or not token:
        return JSONResponse({"error": "invalid_request"}, status_code=400)

    found = await provider.load_access_token(token) or await provider.load_refresh_token(
        client, token
    )

    if found is not None and found.client_id == client.client_id:
        await provider.revoke_token(found)

    return Response(status_code=200, headers={"Cache-Control": "no-store"})


def token_endpoint() -> ASGIApp:
    """/token, the SDK's handler behind a resource check: a request naming another resource
    than the MCP endpoint is refused (invalid_target, RFC 8707), as /authorize refuses it; the
    SDK's handler doesn't pass `resource` on. One naming none is for the MCP endpoint. Every
    other request is counted against the app's token limit before the handler looks its code or
    token up. The form read here is the one the handler reads (Starlette keeps it on the
    request). Wrapped as the SDK wraps its own: CORS outermost, the body's size limited."""
    provider = Provider()
    handler = TokenHandler(provider, ClientAuthenticator(provider))

    async def token(request: Request) -> Response:
        form = await request.form()
        resource = form.get("resource")

        if isinstance(resource, str) and other_resource(resource):
            body = {"error": "invalid_target", "error_description": OTHER_RESOURCE}

            return JSONResponse(body, status_code=400, headers={"Cache-Control": "no-store"})

        client_id = form.get("client_id")

        if isinstance(client_id, str):
            refused = await token_refusal(request, client_id)

            if refused is not None:
                return refused

        return await handler.handle(request)

    limited = RequestBodyLimitMiddleware(request_response(token), DEFAULT_MAX_REQUEST_BODY_SIZE)

    return CORSMiddleware(
        limited,
        allow_origins="*",
        allow_methods=["POST", "OPTIONS"],
        allow_headers=[MCP_PROTOCOL_VERSION_HEADER],
    )


def routes() -> list[Route]:
    """prepza as the authorization server of AI apps, at the site's root (the MCP SDK's
    handlers): its metadata, /authorize (to the consent page), /token, /register and /revoke; and
    the MCP endpoint's resource metadata, which names it."""
    urls = auth_settings()
    issuer = urls.issuer_url
    registration = ClientRegistrationOptions(
        enabled=True, valid_scopes=MCP_SCOPES, default_scopes=[MCP_SCOPE]
    )
    revocation = RevocationOptions(enabled=True)
    metadata = build_metadata(issuer, None, registration, revocation)
    metadata.token_endpoint_auth_methods_supported = AUTH_METHODS
    metadata.revocation_endpoint_auth_methods_supported = AUTH_METHODS
    # Every answer to /authorize names the issuer (services/connections.py, RFC 9207).
    metadata.authorization_response_iss_parameter_supported = True
    # An app may name itself by its metadata document's address instead of registering.
    metadata.client_id_metadata_document_supported = True
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
        elif route.path == TOKEN_PATH:
            route = Route(route.path, endpoint=token_endpoint(), methods=["POST", "OPTIONS"])
        elif route.path == REVOCATION_PATH:
            handler = cors_middleware(revoke, ["POST", "OPTIONS"])
            route = Route(route.path, endpoint=handler, methods=["POST", "OPTIONS"])

        found.append(route)

    resource = create_protected_resource_routes(
        urls.resource_server_url, [issuer], scopes_supported=MCP_SCOPES, resource_name="prepza"
    )
    root = Route(ROOT_RESOURCE_METADATA_PATH, endpoint=resource[0].app, methods=["GET", "OPTIONS"])

    return [*found, *resource, root]
