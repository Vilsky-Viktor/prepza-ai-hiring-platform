"""Every route checks who's asking (prepza_common.auth.route_guards), unless it's public on purpose:
a new route without a guard fails here until it gets one or is listed below with its reason."""

from prepza_common.auth.route_guards import unguarded

from billing.main import app

PUBLIC = {
    # Paddle's web hook: checks Paddle's signature over the raw body.
    "POST /webhooks/paddle",
    "GET /health",
    "GET /ready",
}


def test_every_route_checks_who_is_asking_unless_public_on_purpose():
    assert unguarded(app, PUBLIC, set()) == []
