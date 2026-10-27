from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from prepza_common.http.body_limit import BodyLimitMiddleware


def client(max_bytes=100):
    app = FastAPI()
    app.add_middleware(BodyLimitMiddleware, max_bytes=max_bytes)

    @app.post("/echo")
    async def echo(request: Request):
        return {"size": len(await request.body())}

    return TestClient(app)


def test_a_body_within_the_limit_goes_through():
    response = client().post("/echo", content=b"x" * 100)

    assert (response.status_code, response.json()) == (200, {"size": 100})


def test_a_body_said_to_be_too_large_is_refused_in_the_users_language():
    response = client().post("/echo", content=b"x" * 101, headers={"Accept-Language": "de-DE"})

    assert response.status_code == 413
    assert response.json() == {"detail": "Die Anfrage ist zu groß.", "code": "body_too_large"}


def test_a_streamed_body_is_refused_once_it_grows_too_large():
    def chunks():
        for _ in range(10):
            yield b"x" * 50

    response = client().post("/echo", content=chunks())

    assert response.status_code == 413
    assert response.json() == {"detail": "The request is too large.", "code": "body_too_large"}
