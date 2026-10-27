import asyncio

from prepza_common.events import analytics


def test_events_carry_a_pseudonym_and_never_break_the_caller(monkeypatch):
    sent = []

    async def fake_publish(event_type, data, timeout):
        sent.append((event_type, data, timeout))

    async def broken(event_type, data, timeout):
        raise RuntimeError("pubsub down")

    monkeypatch.setenv("ANALYTICS_SALT", "salt")
    monkeypatch.setattr(analytics, "publish", fake_publish)
    asyncio.run(analytics.track("test_ready", user_id="ann", topics=7))

    [(event_type, data, timeout)] = sent
    assert event_type == "funnel.test_ready"
    # A slow Pub/Sub holds the request no longer than an in-request publish may.
    assert timeout == 5
    assert data["user"] == analytics.pseudonym("ann") != "ann"
    assert data["props"] == {"topics": 7}

    monkeypatch.setattr(analytics, "publish", broken)
    asyncio.run(analytics.track("test_ready", user_id="ann"))


def test_the_same_user_gets_the_same_pseudonym_only_with_the_same_salt(monkeypatch):
    monkeypatch.setenv("ANALYTICS_SALT", "one")
    first = analytics.pseudonym("ann")
    monkeypatch.setenv("ANALYTICS_SALT", "two")

    assert analytics.pseudonym("ann") != first


def test_without_the_key_no_event_about_a_user_is_recorded(monkeypatch, caplog):
    """An unkeyed hash of an id could be matched by anyone holding the ids."""
    sent = []

    async def fake_publish(event_type, data, timeout):
        sent.append(data)

    monkeypatch.setenv("ANALYTICS_SALT", "")
    monkeypatch.setattr(analytics, "publish", fake_publish)
    asyncio.run(analytics.track("signed_up", user_id="ann"))
    asyncio.run(analytics.track("page_seen", company_id="acme"))

    assert analytics.pseudonym("ann") is None
    assert [data["company"] for data in sent] == ["acme"]
    assert "ANALYTICS_SALT isn't set" in caplog.text
