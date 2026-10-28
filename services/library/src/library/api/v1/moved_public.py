"""Library's old public account routes: the account, its settings, email settings, deletion and
download, and the admin zone's email settings and sign-up stats now live in the accounts service
(at /api/accounts/), and the gateway and the load balancer send library's addresses for them
there. These answer only a request that still reaches library during a deploy, sending the browser
to accounts with the same method and body. Kept one release (microservices.md, 3)."""

from fastapi import APIRouter, Request, status
from fastapi.responses import RedirectResponse

from library.constants.accounts_moved import ACCOUNTS_PREFIX

router = APIRouter(include_in_schema=False)


def to_accounts(request: Request) -> RedirectResponse:
    query = f"?{request.url.query}" if request.url.query else ""

    return RedirectResponse(
        f"{ACCOUNTS_PREFIX}{request.url.path}{query}", status.HTTP_307_TEMPORARY_REDIRECT
    )


@router.api_route("/me", methods=["GET", "DELETE"], status_code=307)
def me(request: Request) -> RedirectResponse:
    return to_accounts(request)


@router.api_route("/me/{path:path}", methods=["GET", "PUT"], status_code=307)
def my_settings(path: str, request: Request) -> RedirectResponse:
    """Settings, email settings and the data download."""
    return to_accounts(request)


@router.api_route("/superadmin/emails/{path:path}", methods=["GET", "POST", "PUT"], status_code=307)
def email_settings(path: str, request: Request) -> RedirectResponse:
    return to_accounts(request)


@router.get("/superadmin/stats", status_code=307)
def stats(request: Request) -> RedirectResponse:
    return to_accounts(request)
