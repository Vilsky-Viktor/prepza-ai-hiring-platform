from fastapi import FastAPI
from fastapi.testclient import TestClient
from prepza_common.http.compression import MIN_BYTES, compress_answers
from prepza_common.http.sse import event_stream, sse_event

app = FastAPI()
compress_answers(app)
LARGE = {"names": ["Ann"] * MIN_BYTES}


@app.get("/large")
def large():
    return LARGE


@app.get("/small")
def small():
    return {"name": "Ann"}


@app.get("/stream")
def stream():
    async def events():
        yield sse_event(LARGE)

    return event_stream(events())


client = TestClient(app)
GZIP = {"Accept-Encoding": "gzip"}


def test_a_large_answer_is_gzipped_for_a_client_that_takes_it():
    response = client.get("/large", headers=GZIP)

    assert response.headers["Content-Encoding"] == "gzip"
    assert "Accept-Encoding" in response.headers["Vary"]
    assert response.json() == LARGE


def test_a_client_that_takes_no_gzip_gets_it_plain():
    response = client.get("/large", headers={"Accept-Encoding": "identity"})

    assert "Content-Encoding" not in response.headers
    assert response.json() == LARGE


def test_a_small_answer_stays_plain():
    assert "Content-Encoding" not in client.get("/small", headers=GZIP).headers


def test_a_stream_is_never_compressed():
    response = client.get("/stream", headers=GZIP)

    assert "Content-Encoding" not in response.headers
    assert response.headers["X-Accel-Buffering"] == "no"
    assert response.text == sse_event(LARGE)
