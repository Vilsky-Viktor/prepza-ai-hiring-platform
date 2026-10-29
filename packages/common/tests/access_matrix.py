"""The access matrix (.claude/rules/testing.md, Security): each service's integration test calls
every route that takes the id of something a company or a user owns, against the real database,
as each kind of caller, and compares who got through with who should:

- the owner, with their own ids: let through (anything but 401, 403 or 404; an error from a
  service the test stands in for counts, as the check let the request through);
- the owner of another company (or another user) with the owner's ids: refused (403 or 404);
- on a route with several ids, that other owner with their own ids but one of the owner's, one
  case per id ("cross <id>"): refused, so no id is trusted because another one checks out;
- a viewer of the owner's company: let through to read, refused a change;
- nobody signed in: 401;
- on a superadmin route (each one taking any id), the superadmin is let through and everyone
  else, signed out included, refused (404).

A service's test names the parameters that name something owned (OWNED), makes two sides'
data in its `world` fixture (`enter` signs them in), and lists bodies the models alone can't
make valid (BODIES), values of parameters naming nothing owned (VALUES) and routes that differ
on purpose, with why (EXCEPTIONS: "METHOD path": {caller: outcome}).

It builds on `route_guards` (which finds routes running no guard at all): this one checks the
guard looks at the right object. Routes are found from the app, so a new one is covered as soon
as it exists; a route taking an id of nothing owned (a public token, a page's key) is listed with
why. Users sign in by token (the token is the user's id); calls to other services never leave the
process: companies' access check is answered from the matrix's roles, anything else gets 503.

    ROUTES = access_matrix.routes(app, OWNED, NOT_OWNED)

    @pytest.mark.parametrize("route", ROUTES, ids=str)
    def test_only_whoever_may_gets_through(route, world, run):
        found, statuses = run(access_matrix.outcomes(app, route, world, BODIES, VALUES))

        assert found == access_matrix.expected(route, world, EXCEPTIONS), str(statuses)
"""

import re
from dataclasses import dataclass, field
from uuid import uuid4

import httpx
import request_examples
from fastapi.routing import APIRoute
from firebase_admin import auth as firebase_auth
from prepza_common.auth.route_guards import api_routes, calls
from prepza_common.config.constants import READ_METHODS

ALLOWED, REFUSED, SIGNED_OUT = "allowed", "refused", "signed out"
HOST = "matrix.test"
ACCESS = re.compile(r"/internal/companies/([^/]+)/access$")


@dataclass(frozen=True)
class Route:
    method: str
    path: str
    # The parameters naming something owned, filled from a side's ids.
    owned: tuple[str, ...]
    superadmin: bool
    api: APIRoute = field(compare=False, repr=False)

    def __str__(self):
        return f"{self.method} {self.path}"


@dataclass
class Side:
    """One company's (or one user's) owner, viewer and the ids of what it owns, by parameter."""

    user: str
    ids: dict
    viewer: str | None = None


@dataclass
class World:
    mine: Side
    theirs: Side
    superadmin: str = field(default_factory=lambda: user_id("superadmin"))


def user_id(kind: str) -> str:
    """A fresh user id: each test its own people."""
    return f"matrix-{kind}-{uuid4().hex[:12]}"


def id_params(route) -> list[str]:
    """Every path parameter and every query parameter naming an id."""
    query = [item.name for item in route.dependant.query_params if item.name.endswith("_id")]

    return [item.name for item in route.dependant.path_params] + query


def user_routes(app):
    """Each (method, APIRoute) a user calls: /internal belongs to other services."""
    for route in api_routes(app.routes):
        if not route.path.startswith("/internal"):
            for method in sorted(route.methods):
                yield method, route


def superadmin_only(route) -> bool:
    return "superadmin_user" in calls(route.dependant)


def covered(route, owned: set[str]) -> bool:
    """Whether the matrix calls it: it takes an owned id, or it's a superadmin route taking any
    (refused to everyone else, whatever the id)."""
    names = id_params(route)

    return bool(set(names) & owned) or (bool(names) and superadmin_only(route))


def routes(app, owned: set[str], not_owned: dict[str, str]) -> list[Route]:
    """Every route the matrix calls, but those in `not_owned` ("METHOD path": why)."""
    found = []

    for method, route in user_routes(app):
        if covered(route, owned) and f"{method} {route.path}" not in not_owned:
            mine = tuple(name for name in id_params(route) if name in owned)
            found.append(Route(method, route.path, mine, superadmin_only(route), route))

    return found


def unlisted(app, owned: set[str], not_owned: dict[str, str]) -> list[str]:
    """Routes taking an id the matrix leaves out without a reason, and reasons for routes gone."""
    names = {f"{method} {route.path}": route for method, route in user_routes(app)}
    missing = [
        name
        for name, route in names.items()
        if id_params(route) and not covered(route, owned) and name not in not_owned
    ]

    return missing + [f"gone: {name}" for name in not_owned if name not in names]


def expected(route: Route, world: World, exceptions: dict) -> dict[str, str]:
    """Who should get through, with the route's exceptions ("METHOD path": {caller: outcome})."""
    if route.superadmin:
        found = {"superadmin": ALLOWED, "user": REFUSED, "signed out": REFUSED}
    else:
        found = {"owner": ALLOWED, "outsider": REFUSED, "signed out": SIGNED_OUT}
        found |= {f"cross {name}": REFUSED for name in crossed(route)}

        if world.mine.viewer:
            found["viewer"] = ALLOWED if route.method in READ_METHODS else REFUSED

    return found | exceptions.get(str(route), {})


def crossed(route: Route) -> tuple[str, ...]:
    return route.owned if len(route.owned) > 1 else ()


def callers(route: Route, world: World) -> dict[str, tuple[str | None, dict]]:
    """Each caller with the ids they send; whoever may change things last, as they may."""
    mine, theirs = world.mine, world.theirs

    if route.superadmin:
        return {
            "signed out": (None, mine.ids),
            "user": (mine.user, mine.ids),
            "superadmin": (world.superadmin, mine.ids),
        }

    found = {"signed out": (None, mine.ids), "outsider": (theirs.user, mine.ids)}
    found |= {
        f"cross {name}": (theirs.user, theirs.ids | {name: mine.ids[name]})
        for name in crossed(route)
    }

    if mine.viewer:
        found["viewer"] = (mine.viewer, mine.ids)

    return found | {"owner": (mine.user, mine.ids)}


def outcome(status: int) -> str:
    if status == 401:
        return SIGNED_OUT

    return REFUSED if status in (403, 404) else ALLOWED


def request(route: Route, ids: dict, bodies: dict, values: dict) -> dict:
    """The request's URL and keyword arguments for httpx, filled from `ids` and `values`."""
    path_names = re.findall(r"{(\w+)}", route.path)
    query_names = {item.name for item in route.api.dependant.query_params}
    filled = values | ids
    url = route.path.format(**{name: filled[name] for name in path_names})
    query = request_examples.query(route.api)
    query |= {name: filled[name] for name in query_names & filled.keys()}
    body = bodies.get(str(route))

    if callable(body):
        body = body(ids)

    parts = {"json": body} if body is not None else request_examples.body(route.api)

    return {"method": route.method, "url": url, "params": query, **parts}


async def call_all(app, route: Route, calls: dict, bodies: dict, values: dict):
    """Who got through and the statuses they got, for `calls`: {caller: (headers, ids)}."""
    statuses = {}
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)

    async with httpx.AsyncClient(transport=transport, base_url=f"http://{HOST}") as client:
        for name, (headers, ids) in calls.items():
            response = await client.request(**request(route, ids, bodies, values), headers=headers)
            statuses[name] = response.status_code

    return {name: outcome(status) for name, status in statuses.items()}, statuses


async def outcomes(app, route: Route, world: World, bodies: dict, values: dict):
    """Who got through, by caller, and the statuses they got."""
    calls = {
        name: ({"Authorization": f"Bearer {user}"} if user else {}, ids)
        for name, (user, ids) in callers(route, world).items()
    }

    return await call_all(app, route, calls, bodies, values)


def roles(world: World) -> dict:
    """Who is what in which company (each side's `company_id`), for companies' access check."""
    mine, theirs = world.mine, world.theirs
    found = {(mine.ids.get("company_id"), mine.user): "owner"}
    found[(theirs.ids.get("company_id"), theirs.user)] = "owner"

    if mine.viewer:
        found[(mine.ids.get("company_id"), mine.viewer)] = "viewer"

    return found


def sign_in(monkeypatch, world: World) -> None:
    """A token is its user's id: every user signed in with Google, their email verified, and the
    world's superadmin the only one."""

    def verify_id_token(token, check_revoked=False):
        return {
            "uid": token,
            "email": f"{token}@example.com",
            "email_verified": True,
            "firebase": {"sign_in_provider": "google.com"},
        }

    monkeypatch.setattr(firebase_auth, "verify_id_token", verify_id_token)
    monkeypatch.setenv("SUPERADMIN_EMAILS", f"{world.superadmin}@example.com")


def keep_calls_in(monkeypatch, world: World) -> None:
    """Calls to other services stay in the process: companies' access check answered from the
    world's roles (anyone else isn't a member), anything else a 503."""
    known = roles(world)
    send = httpx.AsyncClient.send

    async def answer(client, request, *args, **kwargs):
        if request.url.host == HOST:
            return await send(client, request, *args, **kwargs)

        if match := ACCESS.search(request.url.path):
            role = known.get((match.group(1), request.url.params.get("user_id")))
            found = {"member": role is not None, "editor": role in ("owner", "admin")}

            return httpx.Response(200, json=found, request=request)

        return httpx.Response(503, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "send", answer)


def enter(monkeypatch, world: World) -> World:
    """The world signed in, its calls kept in; what a service's `world` fixture returns."""
    sign_in(monkeypatch, world)
    keep_calls_in(monkeypatch, world)

    return world
