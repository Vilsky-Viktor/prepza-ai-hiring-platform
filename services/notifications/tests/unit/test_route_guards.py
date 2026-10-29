"""Every route checks who's asking (prepza_common.auth.route_guards), unless it's public on purpose:
a new route without a guard fails here until it gets one or is listed below with its reason."""

from prepza_common.auth.route_guards import not_from_a_service, unguarded

from notifications.main import app

PUBLIC = {
    # Resend's web hook (its Svix signature), Slack's return (a signed one-time state), and the
    # unsubscribe links (each signed).
    "POST /webhooks/resend",
    "GET /slack/callback",
    "GET /unsubscribe/{token}",
    "POST /unsubscribe/{token}",
    "GET /health",
    "GET /ready",
}


def test_every_route_checks_who_is_asking_unless_public_on_purpose():
    assert unguarded(app, PUBLIC, set()) == []


def test_internal_routes_take_only_a_services_token_or_googles_signature():
    assert not_from_a_service(app) == []
