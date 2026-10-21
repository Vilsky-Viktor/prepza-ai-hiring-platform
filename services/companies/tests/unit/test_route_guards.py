"""Every route checks who's asking (prepza_common.route_guards), unless it's public on purpose:
a new route without a guard fails here until it gets one or is listed below with its reason."""

from prepza_common.route_guards import unguarded

from app.main import app

PUBLIC = {
    # Fixed lists and prepza's own brand, the same for everyone.
    "GET /interviews/candidates/filters",
    "GET /brand/prepza",
    # A guest's link is all the guest has: the token is checked, and counted per address.
    "POST /invites/{token}/guest",
    # A logo shows in emails and on candidates' pages: served by its company's id.
    "GET /companies/{company_id}/logo",
    # Whether the emergency pause is on, for the banner.
    "GET /pause",
    "GET /health",
    "GET /ready",
}


def test_every_route_checks_who_is_asking_unless_public_on_purpose():
    assert unguarded(app, PUBLIC, set()) == []
