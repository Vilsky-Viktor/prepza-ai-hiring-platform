"""Every route checks who's asking (prepza_common.auth.route_guards), unless it's public on purpose:
a new route without a guard fails here until it gets one or is listed below with its reason."""

from prepza_common.auth.route_guards import unguarded

from library.main import app

PUBLIC = {
    # The public template library and news, the same for everyone.
    "GET /templates/filters",
    "GET /templates",
    "GET /templates/copyable",
    "GET /templates/{key}",
    "GET /templates/{key}/sample",
    "GET /news",
    # Library's old account addresses, kept one release: each only sends the browser to the same
    # route in accounts (307), which checks who's asking (api/v1/moved_public.py).
    "GET /me",
    "DELETE /me",
    "GET /me/{path:path}",
    "PUT /me/{path:path}",
    "GET /superadmin/emails/{path:path}",
    "POST /superadmin/emails/{path:path}",
    "PUT /superadmin/emails/{path:path}",
    "GET /superadmin/stats",
    "GET /health",
    "GET /ready",
}


def test_every_route_checks_who_is_asking_unless_public_on_purpose():
    assert unguarded(app, PUBLIC, set()) == []
