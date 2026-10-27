from fastapi import Request, status
from fastapi.responses import JSONResponse

from api.constants.permissions import MISSING_PERMISSION, MISSING_PERMISSION_MESSAGE, Permission


class MissingPermission(Exception):
    """The key may not call the route: it doesn't have `permission`."""

    def __init__(self, permission: Permission):
        self.permission = permission


async def missing_permission(request: Request, error: MissingPermission) -> JSONResponse:
    """403 with the code `missing_permission` beside the usual `detail`, which names the
    permission."""
    message = MISSING_PERMISSION_MESSAGE.format(permission=error.permission)

    return JSONResponse(
        {"detail": message, "code": MISSING_PERMISSION}, status_code=status.HTTP_403_FORBIDDEN
    )
