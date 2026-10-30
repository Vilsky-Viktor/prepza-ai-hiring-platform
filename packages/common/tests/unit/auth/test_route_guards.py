"""prepza_common.auth.route_guards finds routes that check no one, also in included routers."""

from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, WebSocket
from prepza_common.auth.auth import CurrentUser
from prepza_common.auth.google import verify_invoker
from prepza_common.auth.route_guards import not_from_a_service, unguarded, websocket_routes
from prepza_common.auth.service_auth import service_caller


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


def test_internal_routes_take_only_a_services_token_or_googles_signature():
    caller = service_caller("library-secret-that-is-at-least-32-bytes", "library")
    app = FastAPI()

    @app.get("/internal/signed")
    def signed(name: caller):
        return {}

    @app.get("/internal/by-a-user")
    def by_a_user(user: CurrentUser):
        return {}

    @app.post("/internal/events", dependencies=[Depends(verify_invoker)])
    def events():
        return {}

    @app.get("/mine")
    def mine(user: CurrentUser):
        return {}

    assert not_from_a_service(app) == ["GET /internal/by-a-user"]


def test_websocket_routes_are_found_also_in_included_routers():
    router = APIRouter(prefix="/things")

    @router.websocket("/{thing_id}/stream")
    async def stream(websocket: WebSocket, thing_id: str):
        await websocket.close()

    @router.get("/mine")
    def mine(user: CurrentUser):
        return {}

    app = FastAPI()
    app.include_router(router)

    @app.websocket("/live")
    async def live(websocket: WebSocket):
        await websocket.close()

    assert websocket_routes(app.routes) == ["/things/{thing_id}/stream", "/live"]
