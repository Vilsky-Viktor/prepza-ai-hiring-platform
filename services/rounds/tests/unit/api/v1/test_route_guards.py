"""Every route checks who's asking (prepza_common.auth.route_guards), unless it's public on purpose:
a new route without a guard fails here until it gets one or is listed below with its reason."""

from prepza_common.auth.route_guards import unguarded

from rounds.main import app

PUBLIC = {
    # A template's public size, and the contact form for visitors (Turnstile and per-address
    # limits); the help chat and its votes, moved to the assistant, and the help pages, moved to
    # site, only send the browser there.
    "GET /practice/{template_id}/size",
    "GET /help/faq",
    "GET /help/guide",
    "GET /help/pages/{key}",
    "GET /help/guides",
    "GET /help/guides/{slug}",
    "GET /help/legal/{document}",
    "POST /help/contact",
    "POST /help/chat",
    "PUT /help/answers/{answer_id}/vote",
    "GET /health",
    "GET /ready",
}


def test_every_route_checks_who_is_asking_unless_public_on_purpose():
    assert unguarded(app, PUBLIC, set()) == []
