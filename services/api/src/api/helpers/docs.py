from fastapi.routing import APIRoute
from starlette.routing import BaseRoute

from api.constants.permissions import Permission
from api.schemas.errors import Error


def route_permission(route: APIRoute) -> Permission | None:
    """The permission a route's key needs (auth.needs), if it declares one."""
    calls = [dependency.call for dependency in route.dependant.dependencies]

    return next((call.permission for call in calls if hasattr(call, "permission")), None)


def name_permissions(routes: list[BaseRoute]) -> None:
    """Adds the permission each public route needs to its description in the API docs."""
    for route in routes:
        permission = isinstance(route, APIRoute) and route_permission(route)

        if permission:
            route.description += f"\n\nNeeds the `{permission}` permission."


def refusal(description: str) -> dict:
    """A refusal's entry in a route's `responses`: its description, with the Error body."""
    return {"model": Error, "description": description}
