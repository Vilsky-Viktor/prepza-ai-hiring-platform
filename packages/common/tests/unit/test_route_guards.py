"""prepza_common.route_guards finds routes that check no one, also in included routers."""

from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI
from prepza_common.auth import CurrentUser
from prepza_common.route_guards import unguarded


def own_key():
    return "key"


def test_routes_without_a_guard_are_found_unless_public():
    router = APIRouter(prefix="/things")

    @router.get("/mine")
    def mine(user: CurrentUser):
        return {}

    @router.get("/open")
    def opened():
        return {}

    @router.post("/keyed")
    def keyed(key: Annotated[str, Depends(own_key)]):
        return {}

    app = FastAPI()
    app.include_router(router)

    @app.get("/health")
    def health():
        return {}

    assert unguarded(app, set()) == ["GET /things/open", "POST /things/keyed", "GET /health"]
    assert unguarded(app, {"GET /health"}, {"own_key"}) == ["GET /things/open"]
