"""Each action whose steps must succeed together is one save: when a later step fails, nothing
the earlier steps wrote is kept, so a retry finds the action whole still to do."""

import socket
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.fernet import Fernet
from prepza_common.auth.encryption import encrypt
from prepza_common.http import public_urls
from sqlalchemy import select, update

from api.config import settings
from api.constants.api import RETRY_GIVE_UP
from api.core.db import Session
from api.integrations import webhooks as endpoints
from api.models.api import WebhookRetry
from api.repositories import keys, webhook_log, webhooks
from api.repositories import webhook_retries as retries
from api.services import accounts
from api.services import webhook_retries as retrying
from api.services import webhooks as delivery
from tests.integration.transactions import transaction

READS = ["interviews:read", "candidates:read"]
BODY = b'{"id":"e1","type":"candidate.finished","data":{}}'


async def broken(*args):
    raise RuntimeError("The database went away")


async def unresolved(url):
    raise socket.gaierror("no such host")


async def new_key(company: uuid.UUID, user: str):
    hashed = uuid.uuid4().hex * 2

    return await transaction(keys.add, company, "Site", "pz_x", hashed, user, None, READS, 10)


async def new_hook(company: uuid.UUID, user: str, secret: str = "sealed"):
    return await transaction(webhooks.add, company, "https://hooks.example.com/x", secret, user, 5)


@pytest.fixture
def reachable(monkeypatch):
    """Web hooks' addresses resolve to a public one and their secrets can be read; the sends go
    nowhere, each taken."""
    key = Fernet.generate_key().decode()
    monkeypatch.setattr(settings, "api_encryption_key", key)
    monkeypatch.setattr(public_urls, "public_address", lambda url: "203.0.113.10")

    async def post(url, address, body, signature):
        pass

    monkeypatch.setattr(endpoints, "post", post)

    return key


def test_a_deleted_account_keeps_everything_when_a_later_step_fails(run, monkeypatch):
    company, user = uuid.uuid4(), f"gone-{uuid.uuid4()}"
    monkeypatch.setattr(webhooks, "remove_user", broken)

    async def scenario():
        await new_key(company, user)
        await new_hook(company, user)

        with pytest.raises(RuntimeError):
            await accounts.remove_user(user, None)

        return await transaction(keys.of_user, user)

    assert len(run(scenario())) == 1


def test_a_deleted_company_keeps_everything_when_a_later_step_fails(run, monkeypatch):
    company = uuid.uuid4()
    monkeypatch.setattr(webhooks, "remove_company", broken)

    async def scenario():
        await new_key(company, "u1")
        await new_hook(company, "u1")

        with pytest.raises(RuntimeError):
            await accounts.remove_company(company)

        return await transaction(keys.of_company, company)

    assert len(run(scenario())) == 1


def test_a_send_that_went_through_is_kept_as_not_sent_when_its_save_fails(
    run, monkeypatch, reachable
):
    """The delivery, its log line and starting the paused web hook again go together."""
    company = uuid.uuid4()
    monkeypatch.setattr(webhooks, "set_failing", broken)

    async def scenario():
        hook = await new_hook(company, "u1", encrypt(reachable, "whsec_a"))
        hook.failing = True

        with pytest.raises(RuntimeError):
            await delivery.deliver(hook, "e1", BODY)

        return (
            await transaction(webhooks.delivered, hook.id, "e1"),
            await transaction(webhook_log.latest, hook.id),
        )

    assert run(scenario()) == (False, [])


def test_an_event_given_up_on_stays_waiting_when_pausing_its_web_hook_fails(run, monkeypatch):
    """Dropping the event and pausing its web hook go together: never one without the other."""
    company = uuid.uuid4()
    long_ago = datetime.now(UTC) - RETRY_GIVE_UP - timedelta(hours=1)
    # Its address doesn't resolve: the send fails again.
    monkeypatch.setattr(delivery, "resolved_address", unresolved)
    monkeypatch.setattr(webhooks, "set_failing", broken)

    async def scenario():
        hook = await new_hook(company, "u1")
        await transaction(retries.add, hook.id, "e1", BODY.decode(), long_ago)

        async with Session.begin() as session:
            await session.execute(
                update(WebhookRetry)
                .where(WebhookRetry.webhook_id == hook.id)
                .values(created_at=long_ago)
            )

        async with Session() as session:
            row = await session.scalar(
                select(WebhookRetry).where(WebhookRetry.webhook_id == hook.id)
            )

        with pytest.raises(RuntimeError):
            await retrying.resend(row, hook, True)

        async with Session() as session:
            return list(
                await session.scalars(
                    select(WebhookRetry.event_id).where(WebhookRetry.webhook_id == hook.id)
                )
            )

    assert run(scenario()) == ["e1"]
