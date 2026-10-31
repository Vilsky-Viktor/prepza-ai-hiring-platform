import asyncio
from types import SimpleNamespace

import httpx
import pytest
from testee_common.auth.encryption import encrypt
from testee_common.events.notifications import NotificationKind, Recipient, notification
from testee_common.http import http

from notifications.config import settings
from notifications.integrations import companies
from notifications.integrations import slack as slack_api
from notifications.repositories import slack as storage
from notifications.services import slack

# The real call to companies, before the fixture stands in for it.
REAL_ACCESS = companies.access
KEY = "Zm9vYmFyYmF6cXV4cXV1eGNvcmdlZ3JhdWx0Z2FycGw="


@pytest.fixture(autouse=True)
def channel(monkeypatch):
    """Slack set up on the server; c1's working channel, which takes candidate_finished, and what
    reaches it."""
    found = {
        "posted": [],
        "broken": [],
        "claimed": set(),
        "answer": None,
        "left": set(),
        "told": [],
    }
    hook = SimpleNamespace(
        kinds=["candidate_finished"], webhook=encrypt(KEY, "https://hooks/x"), created_by="u1"
    )

    async def connected(session, company_id):
        return hook if company_id == "c1" else None

    async def post(webhook, text):
        if found["answer"]:
            raise found["answer"]

        found["posted"].append((webhook, text))

    async def mark_broken(session, company_id):
        stopped = company_id not in found["broken"]
        found["broken"].append(company_id)

        return stopped

    async def add(key, data):
        found["told"].append(data)

        return True

    async def announce(recipient, recipient_id):
        pass

    async def claim(session, key, now):
        new = key not in found["claimed"]
        found["claimed"].add(key)

        return new

    async def release(session, key):
        found["claimed"].discard(key)

    async def access(company_id, user_id):
        return {"member": True, "editor": user_id not in found["left"]}

    monkeypatch.setattr(settings, "slack_client_id", "client")
    monkeypatch.setattr(settings, "slack_client_secret", "secret")
    monkeypatch.setattr(settings, "slack_encryption_key", KEY)
    monkeypatch.setattr(storage, "connected", connected)
    monkeypatch.setattr(storage, "mark_broken", mark_broken)
    monkeypatch.setattr(slack.notices, "store", add)
    monkeypatch.setattr(slack, "announce", announce)
    monkeypatch.setattr(storage, "claim", claim)
    monkeypatch.setattr(storage, "release", release)
    monkeypatch.setattr(slack_api, "post", post)
    monkeypatch.setattr(companies, "access", access)

    return found


def finished(company_id="c1", kind=NotificationKind.CANDIDATE_FINISHED):
    return notification(Recipient.COMPANY, company_id, kind, "/x", email="a@b.c", title="T")


def deliver(event=None, key="e1"):
    asyncio.run(slack.deliver(event or finished(), key))


def test_a_chosen_notification_reaches_the_channel_once(channel):
    deliver()
    deliver()

    assert [webhook for webhook, text in channel["posted"]] == ["https://hooks/x"]


def test_every_event_is_posted_also_one_the_bell_groups(channel):
    deliver(key="e1")
    deliver(key="e2")

    assert len(channel["posted"]) == 2
    assert channel["claimed"] == {"e1", "e2"}


def test_unchosen_kinds_other_companies_and_users_notifications_dont(channel):
    deliver(finished(kind=NotificationKind.INTERVIEW_READY))
    deliver(finished(company_id="c2"))
    deliver(notification(Recipient.USER, "u1", NotificationKind.AUTO_TOP_UP_FAILED, "/"))

    assert channel["posted"] == []
    assert channel["claimed"] == set()


def test_slack_busy_or_down_raises_so_the_retry_posts_it(channel):
    channel["answer"] = slack_api.SlackBusy("429")

    with pytest.raises(slack_api.SlackBusy):
        deliver()

    assert channel["claimed"] == set()

    channel["answer"] = None
    deliver()

    assert len(channel["posted"]) == 1
    assert channel["broken"] == []


def test_a_gone_web_hook_marks_the_channel_and_a_refused_message_is_skipped(channel):
    channel["answer"] = slack_api.WebhookGone()
    deliver(key="e1")
    channel["answer"] = slack_api.SlackRefused("invalid_payload")
    deliver(key="e2")

    assert channel["broken"] == ["c1"]
    # Neither is retried.
    assert channel["claimed"] == {"e1", "e2"}


def test_a_channel_connected_by_someone_no_longer_an_editor_asks_for_reconnecting(channel):
    channel["left"].add("u1")
    deliver()

    assert channel["posted"] == []
    assert channel["broken"] == ["c1"]


def test_a_company_thats_gone_asks_for_reconnecting_instead_of_retrying(channel, monkeypatch):
    def gone(request):
        return httpx.Response(404, json={"detail": "Company not found"})

    monkeypatch.setattr(companies, "access", REAL_ACCESS)
    monkeypatch.setattr(
        http, "get_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(gone))
    )
    deliver()

    assert channel["posted"] == []
    assert channel["broken"] == ["c1"]


def test_the_company_hears_in_the_bell_once_that_its_channel_stopped_working(channel):
    channel["answer"] = slack_api.WebhookGone()

    for _ in range(2):
        asyncio.run(slack.deliver(finished(), f"e-{_}"))

    [told] = channel["told"]
    assert told["kind"] == "connection_broken"
    assert told["data"] == {"name": "Slack", "integration": "slack"}
    assert told["link"] == "/companies/c1/integrations/slack"
