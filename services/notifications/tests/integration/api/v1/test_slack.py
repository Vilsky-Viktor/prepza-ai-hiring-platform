import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.encryption import encrypt
from prepza_common.auth.user import User
from prepza_common.config.constants import DELETED_USER

from notifications.config import settings
from notifications.constants.notifications import KEEP_DAYS
from notifications.constants.slack import SlackStatus
from notifications.core.db import Session
from notifications.helpers.slack import token_hash
from notifications.integrations import companies
from notifications.integrations import slack as slack_api
from notifications.main import app
from notifications.models.slack import SlackPost
from notifications.repositories import notifications
from notifications.repositories import slack as storage
from tests.integration.factories import api, company, finished, push

KEY = "Zm9vYmFyYmF6cXV4cXV1eGNvcmdlZ3JhdWx0Z2FycGw="


async def editor(company_id, user_id):
    return {"member": True, "editor": True}


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    """Slack set up on the server; what's posted and which apps are removed, without Slack."""
    found = {"posted": [], "revoked": [], "down": False}

    async def post(webhook, message):
        if found["down"]:
            raise httpx.ConnectTimeout("Slack is slow")

        # Its text as read: the zero-width space only keeps Slack from linking an email.
        found["posted"].append((webhook, message["text"].replace("\u200b", "")))

    async def revoke(token):
        found["revoked"].append(token)

    monkeypatch.setattr(settings, "slack_client_id", "client")
    monkeypatch.setattr(settings, "slack_client_secret", "secret")
    monkeypatch.setattr(settings, "slack_encryption_key", KEY)
    monkeypatch.setattr(slack_api, "post", post)
    monkeypatch.setattr(slack_api, "revoke", revoke)
    # Whoever connected the channel is still an editor (companies is another service).
    monkeypatch.setattr(companies, "access", editor)

    return found


async def connect(
    company_id, channel="#hiring", kinds=("candidate_finished",), token=None, user_id="u1"
):
    """The company's channel; its workspace's token is its own unless `token` names a shared one."""
    await storage.connect(
        company_id,
        "Acme",
        channel,
        encrypt(KEY, f"https://hooks/{channel}"),
        encrypt(KEY, token or f"token-{company_id}"),
        token_hash(token or f"token-{company_id}"),
        list(kinds),
        user_id,
    )


def test_a_deleted_makers_channel_stays_without_their_id_and_stops_posting(run, configured):
    company_id, maker = company(), f"gone-{uuid.uuid4()}"
    event = push("notification.requested", finished(company_id, email="a@x.com"), "o-d", "m-d")

    async def scenario():
        await connect(company_id, user_id=maker)
        exported = await storage.made_by(maker)
        stopped = await storage.forget_maker(maker)
        # Safe to repeat: it stopped once.
        again = await storage.forget_maker(maker)

        async with api() as client:
            await client.post("/internal/events", json=event)

        found = await storage.get(company_id)

        return exported, found, await storage.made_by(maker), stopped, again

    exported, found, left, stopped, again = run(scenario())

    assert (stopped, again) == ([company_id], [])

    assert [row.company_id for row in exported] == [company_id]
    assert (found.created_by, found.status) == (DELETED_USER, SlackStatus.BROKEN)
    assert left == []
    assert configured["posted"] == []


def test_reconnecting_replaces_the_channel_and_keeps_the_kinds(run):
    company_id = company()

    async def scenario():
        await connect(company_id)
        await storage.set_kinds(company_id, ["interview_ready"], "u1")
        assert await storage.mark_broken(company_id)
        # Already broken: it didn't stop working now.
        assert not await storage.mark_broken(company_id)
        broken = await storage.connected(company_id)
        await connect(company_id, channel="#new", kinds=["candidate_finished"])

        return broken, await storage.get(company_id)

    broken, found = run(scenario())

    assert broken is None
    assert (found.channel, found.status, found.kinds) == (
        "#new",
        SlackStatus.CONNECTED,
        ["interview_ready"],
    )


def test_a_notification_posts_once_however_often_its_event_comes(run, configured):
    company_id = company()
    event = push("notification.requested", finished(company_id, email="a@x.com"), "o-1", "m-s1")

    async def scenario():
        await connect(company_id)

        async with api() as client:
            for _ in range(2):
                await client.post("/internal/events", json=event)

    run(scenario())

    assert [webhook for webhook, text in configured["posted"]] == ["https://hooks/#hiring"]
    assert "a@x.com finished “Backend”" in configured["posted"][0][1]


def test_a_notification_for_an_id_no_company_has_is_handled_not_retried(run, configured):
    # A template's owner, prepza itself, as the library once sent it.
    event = push("notification.requested", finished("prepza"), f"o-{uuid.uuid4()}", "m-s4")

    async def scenario():
        async with api() as client:
            return (await client.post("/internal/events", json=event)).status_code

    assert run(scenario()) < 300
    assert configured["posted"] == []


def test_a_retry_after_slack_was_down_posts_it_without_a_second_bell_notification(run, configured):
    company_id = company()
    event = push("notification.requested", finished(company_id, email="a@x.com"), "o-2", "m-s3")

    async def scenario():
        await connect(company_id)

        async with api() as client:
            configured["down"] = True
            failed = await client.post("/internal/events", json=event)
            configured["down"] = False
            retried = [(await client.post("/internal/events", json=event)) for _ in range(2)]

        bell = await notifications.latest([("company", company_id)], limit=None)

        return failed.status_code, [answer.status_code for answer in retried], len(bell)

    # Pub/Sub retries the failed one; the bell had it from the start.
    assert run(scenario()) == (500, [204, 204], 1)
    assert len(configured["posted"]) == 1


def test_a_burst_grouped_in_the_bell_posts_each_once(run, configured):
    company_id = company()
    bodies = [
        push("notification.requested", finished(company_id, email=f"{n}@x.com"), f"o-g{n}", "m")
        for n in range(3)
    ]

    async def scenario():
        await connect(company_id)

        async with api() as client:
            # Slack fails the first; the rest add to it in the bell; the first's retry posts it,
            # and a retry of one already posted posts nothing.
            configured["down"] = True
            await client.post("/internal/events", json=bodies[0])
            configured["down"] = False

            for body in [*bodies[1:], bodies[0], bodies[1]]:
                await client.post("/internal/events", json=body)

        return await notifications.latest([("company", company_id)], limit=None)

    [bell] = run(scenario())

    assert bell.data["count"] == 3
    posted = sorted(text.split(" finished")[0] for _, text in configured["posted"])
    assert posted == ["0@x.com", "1@x.com", "2@x.com"]


def test_a_deleted_companys_channel_and_app_go(run, configured):
    company_id = company()
    deleted = push("company.deleted", {"company_id": company_id}, message_id="m-s2")

    async def scenario():
        await connect(company_id)

        async with api() as client:
            await client.post("/internal/events", json=deleted)

        return await storage.get(company_id)

    assert run(scenario()) is None
    assert configured["revoked"] == [f"token-{company_id}"]


def test_the_app_stays_while_another_company_uses_its_workspace(run, configured):
    first, second = company(), company()
    shared = f"token-{first}"

    async def scenario():
        await connect(first, token=shared)
        await connect(second, token=shared)

        async with api() as client:
            await client.post("/internal/events", json=gone(first, "m-s4"))
            kept = list(configured["revoked"])
            await client.post("/internal/events", json=gone(second, "m-s5"))

        return kept

    assert run(scenario()) == []
    assert configured["revoked"] == [shared]


def gone(company_id, message_id):
    return push("company.deleted", {"company_id": company_id}, message_id=message_id)


def test_an_add_to_slack_trip_finishes_once(run, monkeypatch):
    company_id = company()

    async def exchange(code):
        return {"team": "Acme", "channel": "#hiring", "url": "https://hooks/x", "token": "t"}

    monkeypatch.setattr(slack_api, "exchange", exchange)
    app.dependency_overrides[current_user] = lambda: User(
        uid="u1", email="u1@example.com", email_verified=True, name="Ann"
    )

    async def scenario():
        async with api() as client:
            started = await client.get(f"/slack/start?company_id={company_id}")
            state = parse_qs(urlparse(started.json()["url"]).query)["state"][0]

            return [
                (await client.get(f"/slack/callback?code=ok&state={state}")).status_code
                for _ in range(2)
            ]

    try:
        assert run(scenario()) == [303, 422]
    finally:
        app.dependency_overrides.clear()


def test_a_slack_mark_is_taken_once_freed_on_failure_and_pruned_when_expired(run):
    old_key, key = f"old-{company()}", f"new-{company()}"

    async def scenario():
        async with Session() as session:
            expired = datetime.now(UTC) - timedelta(days=KEEP_DAYS + 1)
            session.add(SlackPost(event_id=old_key, posted_at=expired))
            await session.commit()

        taken = [await storage.claim(key), await storage.claim(key)]
        await storage.release(key)
        taken.append(await storage.claim(key))

        async with Session() as session:
            return taken, await session.get(SlackPost, old_key)

    assert run(scenario()) == ([True, False, True], None)
