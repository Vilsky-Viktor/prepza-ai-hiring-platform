"""Every route checks who's asking (prepza_common.route_guards), unless it's public on purpose:
a new route without a guard fails here until it gets one or is listed below with its reason."""

from prepza_common.route_guards import unguarded

from app.main import app

PUBLIC = {
    # The public template library and news, the same for everyone.
    "GET /templates/filters",
    "GET /templates",
    "GET /templates/copyable",
    "GET /templates/{key}",
    "GET /templates/{key}/sample",
    "GET /news",
    "GET /health",
    "GET /ready",
}


def test_every_route_checks_who_is_asking_unless_public_on_purpose():
    assert unguarded(app, PUBLIC, set()) == []
