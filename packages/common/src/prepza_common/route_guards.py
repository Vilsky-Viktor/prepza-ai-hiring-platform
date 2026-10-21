"""Every route has an access check (the security rules): a test of each service walks its app's
routes and lists any that runs none of the guards, unless it's public on purpose."""

from fastapi import FastAPI
from fastapi.routing import APIRoute

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


def unguarded(app: FastAPI, public: set[str], extra: set[str] = frozenset()) -> list[str]:
    """Each "METHOD path" of `app` whose dependencies run no guard and isn't in `public` (a path
    as its router names it)."""
    found = []

    for route in api_routes(app.routes):
        names = calls(route.dependant) | {
            getattr(dependency.dependency, "__name__", "") for dependency in route.dependencies
        }

        for method in sorted(route.methods):
            name = f"{method} {route.path}"

            if not names & (GUARDS | extra) and name not in public:
                found.append(name)

    return found
