"""Every route checks who's asking (testee_common.auth.route_guards), unless it's public on purpose:
a new route without a guard fails here until it gets one or is listed below with its reason."""

from testee_common.auth.route_guards import not_from_a_service, unguarded, websocket_routes

from rounds.main import app

PUBLIC = {
    # A template's public size.
    "GET /practice/{template_id}/size",
    "GET /health",
    "GET /ready",
}
# WebSocket routes, which take no headers, and how each signs its caller in.
WEBSOCKETS = {
    # The first message's Firebase token, checked as a write's (services/voice_stream.py
    # signed_in); then the candidate's own session (test_voice_stream.py).
    "/sessions/{session_id}/voice/stream": "first message",
}


def test_every_route_checks_who_is_asking_unless_public_on_purpose():
    assert unguarded(app, PUBLIC, set()) == []


def test_internal_routes_take_only_a_services_token_or_googles_signature():
    assert not_from_a_service(app) == []


def test_every_websocket_route_names_how_it_signs_in():
    assert websocket_routes(app.routes) == list(WEBSOCKETS)
