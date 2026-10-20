from fastapi import FastAPI, Response
from fastapi.testclient import TestClient
from prepza_common.no_store import NoStoreMiddleware

app = FastAPI()
app.add_middleware(NoStoreMiddleware)


@app.get("/mine")
def mine():
    return {"email": "ann@example.com"}


@app.get("/logo")
def logo():
    return Response(b"png", headers={"Cache-Control": "public, max-age=60"})


client = TestClient(app)
SIGNED_IN = {"Authorization": "Bearer token"}


def test_a_signed_in_answer_is_kept_by_no_cache():
    assert client.get("/mine", headers=SIGNED_IN).headers["Cache-Control"] == "no-store"


def test_a_routes_own_cache_control_stays():
    assert client.get("/logo", headers=SIGNED_IN).headers["Cache-Control"] == "public, max-age=60"


def test_an_anonymous_answer_is_left_to_its_route():
    assert "Cache-Control" not in client.get("/mine").headers
