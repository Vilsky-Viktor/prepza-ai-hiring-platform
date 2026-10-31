"""Every route has an access check (the security rules): a test of each service walks its app's
routes and lists any that runs none of the guards, unless it's public on purpose."""

from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.routing import WebSocketRoute

# The dependencies that check who's asking: a signed-in user (or one optional on a public page
# that checks a link itself), a superadmin, another service, Google's pushes and jobs, and an
# API key. Services add their own (`extra`).
GUARDS = {
    "current_user",
    "optional_user",
    "fresh_user",
    "superadmin_user",
    "verify_service",
    "verify_invoker",
}
# Who may call /internal: another service with its token, or Google (Pub/Sub, Scheduler).
INTERNAL_GUARDS = {"verify_service", "verify_invoker"}


def calls(dependant) -> set[str]:
    """The names of every function a route's dependencies run, however deep."""
    found = {getattr(dependant.call, "__name__", "")}

    for child in dependant.dependencies:
        found |= calls(child)

    return found


def api_routes(routes) -> list[APIRoute]:
    """Every APIRoute, also those of included routers (FastAPI keeps each included router as one
    route, its own routes under `original_router`)."""
    found = []

    for route in routes:
        if isinstance(route, APIRoute):
            found.append(route)
        elif hasattr(route, "original_router"):
            found += api_routes(route.original_router.routes)

    return found


def guards_run(route: APIRoute) -> set[str]:
    """The names of what a route runs: its parameters' dependencies and its router's."""
    return calls(route.dependant) | {
        getattr(dependency.dependency, "__name__", "") for dependency in route.dependencies
    }


def unguarded(app: FastAPI, public: set[str], extra: set[str] = frozenset()) -> list[str]:
    """Each "METHOD path" of `app` whose dependencies run no guard and isn't in `public` (a path
    as its router names it)."""
    found = []

    for route in api_routes(app.routes):
        names = guards_run(route)

        for method in sorted(route.methods):
            name = f"{method} {route.path}"

            if not names & (GUARDS | extra) and name not in public:
                found.append(name)

    return found


def not_from_a_service(app: FastAPI) -> list[str]:
    """Each "METHOD path" under /internal (blocked at the edge, for other services and Google's
    pushes and jobs only) that checks neither a service token nor Google's signature."""
    found = []

    for route in api_routes(app.routes):
        names = guards_run(route)

        if route.path.startswith("/internal") and not names & INTERNAL_GUARDS:
            found += [f"{method} {route.path}" for method in sorted(route.methods)]

    return found


def websocket_routes(routes) -> list[str]:
    """The path of every WebSocket route, also in included routers. A browser can't give a
    WebSocket headers, so none runs a header's guard and `unguarded` doesn't see them: each signs
    in its own way, which its service's test names, so a new one fails there until it's
    listed."""
    found = []

    for route in routes:
        if isinstance(route, WebSocketRoute):
            found.append(route.path)
        elif hasattr(route, "original_router"):
            found += websocket_routes(route.original_router.routes)

    return found
