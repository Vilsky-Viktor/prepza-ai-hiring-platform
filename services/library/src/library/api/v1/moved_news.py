"""Library's old public news routes: the news page and the admin zone's news tab now live in the
site service (at /api/site/), and the gateway and the load balancer send library's addresses for
them there. These answer only a request that still reaches library during a deploy, sending the
browser to site with the same method and body. Kept one release (microservices.md, 3)."""

from fastapi import APIRouter, Request, status
from fastapi.responses import RedirectResponse

from library.constants.site_moved import SITE_PREFIX

router = APIRouter(include_in_schema=False)


def to_site(request: Request) -> RedirectResponse:
    query = f"?{request.url.query}" if request.url.query else ""

    return RedirectResponse(
        f"{SITE_PREFIX}{request.url.path}{query}", status.HTTP_307_TEMPORARY_REDIRECT
    )


@router.get("/news", status_code=307)
def news(request: Request) -> RedirectResponse:
    return to_site(request)


@router.api_route("/superadmin/news", methods=["GET", "POST"], status_code=307)
def admin_news(request: Request) -> RedirectResponse:
    return to_site(request)


@router.api_route("/superadmin/news/{news_id}", methods=["PUT", "DELETE"], status_code=307)
def admin_post(news_id: str, request: Request) -> RedirectResponse:
    return to_site(request)
