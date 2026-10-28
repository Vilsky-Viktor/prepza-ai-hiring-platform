"""Every route checks who's asking (prepza_common.auth.route_guards), unless it's public on purpose:
a new route without a guard fails here until it gets one or is listed below with its reason."""

from prepza_common.auth.route_guards import unguarded

from assistant.main import app

PUBLIC = {
    # The panel's limits, asked signed out too.
    "GET /config",
    # A vote on a help chat answer, for visitors too: it carries its answer's signature.
    "PUT /help/answers/{answer_id}/vote",
    # What AI apps may call, listed for the public docs; uptime checks.
    "GET /mcp/tools",
    "GET /health",
    "GET /ready",
}


def test_every_route_checks_who_is_asking_unless_public_on_purpose():
    assert unguarded(app, PUBLIC, {"user_with_token"}) == []
