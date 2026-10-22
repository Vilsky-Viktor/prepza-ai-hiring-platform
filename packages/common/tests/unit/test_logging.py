import json
import logging
import sys
from datetime import datetime

from fastapi import FastAPI, Response
from fastapi.testclient import TestClient
from prepza_common.constants import TRACE_FIELD, TRACE_HEADER
from prepza_common.logging import JsonFormatter, RequestLogMiddleware, configure_logging, trace_of


def test_outgoing_request_addresses_are_not_logged(caplog):
    """A Slack web hook's address lets anyone post to the channel: the HTTP client's request
    lines, which hold it, stay out of the logs."""
    configure_logging()

    with caplog.at_level(logging.INFO):
        logging.getLogger("httpx").info("HTTP Request: POST https://hooks.slack.com/services/T/B/x")

    assert "hooks.slack.com" not in caplog.text
    assert logging.getLogger("httpx").getEffectiveLevel() == logging.WARNING


def record(level=logging.ERROR):
    return logging.LogRecord("billing", level, __file__, 1, "refused: %s", ("paddle",), None)


def test_a_line_carries_the_fields_cloud_logging_reads():
    line = json.loads(JsonFormatter().format(record()))

    assert (line["severity"], line["message"], line["logger"]) == (
        "ERROR",
        "refused: paddle",
        "billing",
    )
    assert TRACE_FIELD not in line
    assert datetime.fromisoformat(line["time"]).tzinfo is not None


def test_uvicorns_own_lines_are_json_too(capsys):
    """Uvicorn sets up its logger with a plain-text handler before the app loads; once the app's
    logging is configured, its lines (an unhandled error's traceback) are JSON with a severity."""
    server = logging.getLogger("uvicorn")
    server.addHandler(logging.StreamHandler(sys.stdout))
    server.propagate = False
    configure_logging()

    logging.getLogger("uvicorn.error").error("Exception in ASGI application")
    lines = [line for line in capsys.readouterr().err.splitlines() if line]

    assert json.loads(lines[-1])["severity"] == "ERROR"
    assert capsys.readouterr().out == ""


def test_emails_and_url_paths_never_reach_a_line_even_from_an_error():
    try:
        raise ValueError('Key (email)=(ann@example.com) exists; url "https://hooks.slack.com/T/x"')
    except ValueError:
        error = sys.exc_info()

    item = logging.LogRecord("x", logging.ERROR, __file__, 1, "for %s", ("bo@example.com",), error)
    line = json.loads(JsonFormatter().format(item))

    assert line["message"] == "for [email]"
    assert "Key (email)=([email]) exists" in line["exc"]
    assert '"https://hooks.slack.com"' in line["exc"]
    assert "example.com" not in line["exc"]


def test_the_trace_comes_from_the_load_balancers_header(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "prepza-prod")

    assert trace_of("abc123/456;o=1") == "projects/prepza-prod/traces/abc123"
    assert trace_of(None) is None
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT")
    assert trace_of("abc123/456;o=1") is None


def test_a_requests_line_names_its_route_never_the_token_in_its_path():
    lines = []

    class Capture(logging.Handler):
        def emit(self, item):
            if item.name == "http":
                lines.append(item.getMessage())

    app = FastAPI()
    app.add_middleware(RequestLogMiddleware)

    @app.get("/invites/{token}")
    def invite(token: str):
        return {}

    handler = Capture()
    logging.getLogger().addHandler(handler)

    try:
        client = TestClient(app)
        client.get("/invites/secret-token-123?x=1")
        client.get("/nothing/secret-token-456")
    finally:
        logging.getLogger().removeHandler(handler)

    assert lines[0].startswith("GET /invites/{token} 200 ")
    assert lines[1].startswith("GET (no route) 404 ")
    assert not any("secret-token" in line for line in lines)


def test_a_refused_sign_in_or_permission_is_a_warning():
    levels = {}

    class Capture(logging.Handler):
        def emit(self, item):
            if item.name == "http":
                levels[item.getMessage().split()[2]] = item.levelname

    app = FastAPI()
    app.add_middleware(RequestLogMiddleware)

    @app.get("/answer/{code}")
    def answer(code: int):
        return Response(status_code=code)

    handler = Capture()
    logging.getLogger().addHandler(handler)

    try:
        for code in (200, 401, 403, 404):
            TestClient(app).get(f"/answer/{code}")
    finally:
        logging.getLogger().removeHandler(handler)

    assert levels == {"200": "INFO", "401": "WARNING", "403": "WARNING", "404": "INFO"}


def test_uvicorns_access_log_is_off():
    configure_logging()

    assert logging.getLogger("uvicorn.access").disabled


def test_lines_logged_during_a_request_carry_its_trace(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "prepza-prod")
    lines = []

    class Capture(logging.Handler):
        def emit(self, item):
            lines.append(json.loads(JsonFormatter().format(item)))

    app = FastAPI()
    app.add_middleware(RequestLogMiddleware)

    @app.get("/work")
    def work():
        logging.getLogger("work").warning("working")

        return {}

    handler = Capture()
    logging.getLogger().addHandler(handler)

    try:
        TestClient(app).get("/work", headers={TRACE_HEADER: "abc123/1;o=1"})
    finally:
        logging.getLogger().removeHandler(handler)

    traced = [line for line in lines if line["message"] == "working"]
    assert traced[0][TRACE_FIELD] == "projects/prepza-prod/traces/abc123"
    # Outside the request, nothing carries it.
    assert TRACE_FIELD not in json.loads(JsonFormatter().format(record()))
