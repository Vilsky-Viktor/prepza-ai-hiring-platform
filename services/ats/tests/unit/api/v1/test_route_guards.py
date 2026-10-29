"""Every route checks who's asking (prepza_common.auth.route_guards), unless it's public on purpose:
a new route without a guard fails here until it gets one or is listed below with its reason."""

from prepza_common.auth.route_guards import not_from_a_service, unguarded

from ats.main import app

PUBLIC = {
    # The ATSs' web hooks: each checks its HMAC signature over the raw body.
    "POST /webhooks/workable/{link_id}",
    "POST /webhooks/greenhouse/{connection_id}",
    "POST /webhooks/teamtailor/{connection_id}",
    "POST /webhooks/recruitee/{connection_id}",
    "POST /webhooks/breezy/{connection_id}",
    "GET /health",
    "GET /ready",
}


def test_every_route_checks_who_is_asking_unless_public_on_purpose():
    assert unguarded(app, PUBLIC, set()) == []


def test_internal_routes_take_only_a_services_token_or_googles_signature():
    assert not_from_a_service(app) == []
