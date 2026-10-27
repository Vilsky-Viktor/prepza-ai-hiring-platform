from fastapi import FastAPI, Response
from fastapi.testclient import TestClient
from prepza_common.http.no_store import NoStoreMiddleware

app = FastAPI()
app.add_middleware(NoStoreMiddleware)


@app.get("/mine")
def mine():
    return {"email": "ann@example.com"}


@app.get("/logo")
def logo():
    return Response(b"png", headers={"Cache-Control": "public, max-age=60"})


@app.get("/invites/{token}")
def invite(token: str):
    return {"email": "ann@example.com"}


client = TestClient(app)
SIGNED_IN = {"Authorization": "Bearer token"}


def test_a_signed_in_answer_is_kept_by_no_cache():
    assert client.get("/mine", headers=SIGNED_IN).headers["Cache-Control"] == "no-store"


def test_a_routes_own_cache_control_stays():
    assert client.get("/logo", headers=SIGNED_IN).headers["Cache-Control"] == "public, max-age=60"


def test_an_anonymous_answer_is_left_to_its_route():
    assert "Cache-Control" not in client.get("/mine").headers


def test_an_answer_to_a_secret_links_path_is_never_kept_though_anonymous():
    assert client.get("/invites/abc").headers["Cache-Control"] == "no-store"
