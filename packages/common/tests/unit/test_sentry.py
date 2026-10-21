from unittest import mock

import sentry_sdk
from prepza_common import sentry
from prepza_common.sentry import init_sentry, traces_sampler


def test_nothing_is_sent_without_a_dsn(monkeypatch):
    monkeypatch.delenv("BACKEND_SENTRY_DSN", raising=False)

    with mock.patch.object(sentry_sdk, "init") as init:
        init_sentry("rounds")

    init.assert_not_called()


def test_with_a_dsn_no_personal_data_is_sent(monkeypatch):
    monkeypatch.setenv("BACKEND_SENTRY_DSN", "https://key@example.ingest.sentry.io/1")

    with mock.patch.object(sentry_sdk, "init") as init:
        init_sentry("rounds")

    options = init.call_args.kwargs
    assert options["send_default_pii"] is False
    assert options["max_request_body_size"] == "never"
    assert options["server_name"] == "rounds"
    assert options["before_send"] is sentry.before_send
    assert options["before_send_transaction"] is sentry.before_send


def test_stack_traces_carry_no_variables_values(monkeypatch):
    """They would hold secrets (ATS keys, Slack tokens) and people's texts."""
    monkeypatch.setenv("BACKEND_SENTRY_DSN", "https://key@sentry.example/1")

    with mock.patch.object(sentry_sdk, "init") as init:
        init_sentry("ats")

    assert init.call_args.kwargs["include_local_variables"] is False


def test_uptime_checks_jobs_and_events_are_not_traced_on_their_own(monkeypatch):
    monkeypatch.setenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")

    for path in ("/ready", "/health", "/internal/schedules/outbox", "/internal/events"):
        assert traces_sampler({"asgi_scope": {"path": path}}) == 0.0

    assert traces_sampler({"asgi_scope": {"path": "/interviews"}}) == 0.1
    assert traces_sampler({"asgi_scope": {"path": "/internalize"}}) == 0.1


def test_a_call_inside_a_traced_request_follows_it(monkeypatch):
    monkeypatch.setenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")
    internal = {"asgi_scope": {"path": "/internal/users/1"}}

    assert traces_sampler({**internal, "parent_sampled": True}) == 1.0
    assert traces_sampler({"asgi_scope": {"path": "/me"}, "parent_sampled": False}) == 0.0


def test_the_sampler_is_used(monkeypatch):
    monkeypatch.setenv("BACKEND_SENTRY_DSN", "https://key@sentry.example/1")

    with mock.patch.object(sentry_sdk, "init") as init:
        init_sentry("rounds")

    assert init.call_args.kwargs["traces_sampler"] is sentry.traces_sampler
