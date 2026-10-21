import json
import socket
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import httpx
import pytest
from prepza_common.encryption import encrypt

from app.services import webhooks as delivery
from tests.unit.ids import COMPANY, KEY


@pytest.fixture
def endpoints(monkeypatch, companies_api):
    """COMPANY's web hooks, what each endpoint got, which fail or don't resolve, which got which
    event, and the events kept for the retry job (by web hook and event)."""
    state = {
        "hooks": [],
        "posted": [],
        "failing": set(),
        "delivered": set(),
        "public": True,
        "unresolved": set(),
        "retries": {},
        "told": [],
        "log": [],
    }

    def hook(url, secret="whsec_a", maker="u1"):
        found = SimpleNamespace(
            id=uuid.uuid4(),
            company_id=COMPANY,
            url=url,
            secret=encrypt(KEY, secret),
            created_by=maker,
            failing=False,
            stopped=False,
        )
        state["hooks"].append(found)

        return found

    async def of_company(company_id):
        return state["hooks"] if company_id == COMPANY else []

    async def delivered(webhook_id, event_id):
        return (webhook_id, event_id) in state["delivered"]

    async def delivered_to(webhook_ids, event_id):
        return {item for item in webhook_ids if (item, event_id) in state["delivered"]}

    async def mark_delivered(webhook_id, event_id):
        state["delivered"].add((webhook_id, event_id))

    async def set_failing(webhook_id, failing):
        next(item for item in state["hooks"] if item.id == webhook_id).failing = failing

    async def set_stopped(webhook_id, stopped, notice=None):
        found = next(item for item in state["hooks"] if item.id == webhook_id)
        changed = found.stopped != stopped
        found.stopped = stopped

        if changed and notice is not None:
            state["told"].append(notice)

        return changed

    async def post(url, address, body, signature):
        if url in state["failing"]:
            raise httpx.ConnectError("down")

        state["posted"].append((url, json.loads(body), signature))

    async def add_retry(webhook_id, event_id, body, next_at):
        state["retries"].setdefault(
            (webhook_id, event_id),
            SimpleNamespace(
                event_id=event_id,
                body=body,
                attempts=1,
                next_at=next_at,
                created_at=datetime.now(UTC),
            ),
        )

    async def claim(limit):
        now = datetime.now(UTC)
        hooks = {item.id: item for item in state["hooks"]}
        due = [
            (row, hooks[webhook_id])
            for (webhook_id, _), row in state["retries"].items()
            if row.next_at <= now
        ]

        return due[:limit]

    async def postpone(webhook_id, event_id, attempts, next_at):
        row = state["retries"][(webhook_id, event_id)]
        row.attempts, row.next_at = attempts, next_at

    async def remove_retry(webhook_id, event_id):
        state["retries"].pop((webhook_id, event_id))

    async def log(webhook_id, event_id, event_type, ok, result):
        state["log"].append((webhook_id, event_type, ok, result))

    monkeypatch.setattr(delivery.webhook_log, "add", log)
    monkeypatch.setattr(delivery.webhooks, "of_company", of_company)
    monkeypatch.setattr(delivery.webhooks, "delivered", delivered)
    monkeypatch.setattr(delivery.webhooks, "delivered_to", delivered_to)
    monkeypatch.setattr(delivery.webhooks, "mark_delivered", mark_delivered)
    monkeypatch.setattr(delivery.webhooks, "set_failing", set_failing)
    monkeypatch.setattr(delivery.webhooks, "set_stopped", set_stopped)
    monkeypatch.setattr(delivery.endpoints, "post", post)
    monkeypatch.setattr(delivery.retries, "add", add_retry)
    monkeypatch.setattr(delivery.retries, "claim", claim)
    monkeypatch.setattr(delivery.retries, "postpone", postpone)
    monkeypatch.setattr(delivery.retries, "remove", remove_retry)
    monkeypatch.setattr(delivery, "public_address", lambda url: check(url, state))
    state["hook"] = hook

    return state


def check(url, state):
    """public_address, faked: an address in state["unresolved"] doesn't resolve."""
    if url in state["unresolved"]:
        raise socket.gaierror

    return "203.0.113.10" if state["public"] else None
