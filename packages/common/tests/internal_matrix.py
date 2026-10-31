"""The access matrix of /internal routes (.claude/rules/testing.md, Security): the routes other
services call with a service token, and that take an id together with the id that scopes it (an
interview and its company, a question and its set, a sender and the interview they invite to).
The caller vouches for the scope (the public API for its key's company, companies for its
member's interview); the route must still refuse an object outside it. Each is called, against
the real database, with:

- a token for this service and one side's ids: let through (anything but 401, 403 or 404);
- that token and the same ids but one from the other side, one case per id ("cross <id>"):
  refused (403 or 404);
- no token, and a token signed with this service's key for another service ("wrong audience"):
  refused (401).

Routes are found from the app, as `access_matrix` finds the user's: a route with two or more ids
(in its path or query, or in its body as the test names them, `body_ids`) is called, or listed
with why it scopes nothing (an acting user the caller vouches for, a filter). It reuses
`access_matrix`'s sides, requests and outcomes; a service's `world` fixture serves both.

    ROUTES = internal_matrix.routes(app, OWNED, NOT_SCOPED, BODY_IDS)

    @pytest.mark.parametrize("route", ROUTES, ids=str)
    def test_only_the_scoped_object_gets_through(route, world, run):
        found, statuses = run(internal_matrix.outcomes(app, route, world, KEY, BODIES, VALUES))

        assert found == internal_matrix.expected(route, {}), str(statuses)
"""

from access_matrix import ALLOWED, REFUSED, SIGNED_OUT, Route, World, call_all, id_params
from testee_common.auth.route_guards import api_routes, calls
from testee_common.auth.service_auth import issue_token
from testee_common.http.http import bearer


def service_routes(app):
    """Each (method, APIRoute) under /internal that takes a service token."""
    for route in api_routes(app.routes):
        if route.path.startswith("/internal") and "verify_service" in calls(route.dependant):
            for method in sorted(route.methods):
                yield method, route


def ids_of(name: str, route, body_ids: dict) -> list[str]:
    return id_params(route) + list(body_ids.get(name, ()))


def routes(app, owned: set[str], not_scoped: dict[str, str], body_ids: dict) -> list[Route]:
    """Every service route taking two or more owned ids, but those in `not_scoped`."""
    found = []

    for method, route in service_routes(app):
        name = f"{method} {route.path}"
        mine = tuple(item for item in ids_of(name, route, body_ids) if item in owned)

        if len(mine) > 1 and name not in not_scoped:
            found.append(Route(method, route.path, mine, False, route))

    return found


def unlisted(app, owned: set[str], not_scoped: dict[str, str], body_ids: dict) -> list[str]:
    """Service routes taking two or more ids the matrix leaves out without a reason, and reasons
    for routes gone."""
    names = {f"{method} {route.path}": route for method, route in service_routes(app)}
    missing = [
        name
        for name, route in names.items()
        if len(ids_of(name, route, body_ids)) > 1
        and len(set(ids_of(name, route, body_ids)) & owned) < 2
        and name not in not_scoped
    ]

    return missing + [f"gone: {name}" for name in not_scoped if name not in names]


def expected(route: Route, exceptions: dict) -> dict[str, str]:
    found = {"service": ALLOWED, "no token": SIGNED_OUT, "wrong audience": SIGNED_OUT}
    found |= {f"cross {name}": REFUSED for name in route.owned}

    return found | exceptions.get(str(route), {})


async def outcomes(app, route: Route, world: World, key: tuple, bodies: dict, values: dict):
    """Who got through and the statuses they got; `key` is the service's (secret, name)."""
    secret, name = key
    token = bearer(issue_token("matrix", name, secret))
    wrong = bearer(issue_token("matrix", f"not-{name}", secret))
    mine, theirs = world.mine.ids, world.theirs.ids
    found = {"no token": ({}, mine), "wrong audience": (wrong, mine)}
    found |= {f"cross {item}": (token, mine | {item: theirs[item]}) for item in route.owned}

    return await call_all(app, route, found | {"service": (token, mine)}, bodies, values)
