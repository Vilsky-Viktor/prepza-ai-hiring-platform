"""Every route checks who's asking (prepza_common.auth.route_guards), unless it's public on purpose:
a new route without a guard fails here until it gets one or is listed below with its reason."""

from prepza_common.auth.route_guards import unguarded

from site_content.main import app

PUBLIC = {
    "GET /health",
    "GET /ready",
}


def test_every_route_checks_who_is_asking_unless_public_on_purpose():
    assert unguarded(app, PUBLIC, set()) == []
