"""Rounds' old public content routes: the FAQ, page guides, guide articles, legal texts and the
contact form now live in the site service (at /api/site/), and the gateway and the load balancer send rounds'
addresses for them there. These answer only a request that still reaches rounds during a
deploy, sending the browser to site with the same method and body. Kept one release (microservices.md,
3)."""

from fastapi import APIRouter, Request, status
from fastapi.responses import RedirectResponse

from rounds.constants.site_moved import SITE_PREFIX

router = APIRouter(prefix="/help", include_in_schema=False)


def to_site(request: Request) -> RedirectResponse:
    query = f"?{request.url.query}" if request.url.query else ""

    return RedirectResponse(
        f"{SITE_PREFIX}{request.url.path}{query}", status.HTTP_307_TEMPORARY_REDIRECT
    )


@router.get("/faq", status_code=307)
def faq(request: Request) -> RedirectResponse:
    return to_site(request)


@router.get("/guide", status_code=307)
def platform_guide(request: Request) -> RedirectResponse:
    return to_site(request)


@router.get("/pages/{key}", status_code=307)
def page_guide(key: str, request: Request) -> RedirectResponse:
    return to_site(request)


@router.get("/guides", status_code=307)
def guides(request: Request) -> RedirectResponse:
    return to_site(request)


@router.get("/guides/{slug}", status_code=307)
def guide(slug: str, request: Request) -> RedirectResponse:
    return to_site(request)


@router.get("/legal/{document}", status_code=307)
def legal_text(document: str, request: Request) -> RedirectResponse:
    return to_site(request)


@router.post("/contact", status_code=307)
def contact(request: Request) -> RedirectResponse:
    return to_site(request)
