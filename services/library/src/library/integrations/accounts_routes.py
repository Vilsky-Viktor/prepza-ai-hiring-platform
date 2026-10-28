from fastapi import Request, Response
from prepza_common.http import http
from prepza_common.http.http import bearer

from library.config import settings
from library.core.security import service_token


async def forward(request: Request) -> Response:
    """The same call to accounts, which holds what this route served, and its answer as it is
    (a 404 included). For library's old account routes, kept one release for callers that still
    use them (microservices.md, 3)."""
    response = await http.get_client().request(
        request.method,
        f"{settings.accounts_url}{request.url.path}",
        params=request.query_params,
        content=await request.body(),
        headers={"Content-Type": "application/json", **bearer(service_token("accounts"))},
    )

    return Response(
        response.content, response.status_code, media_type=response.headers.get("content-type")
    )
