import asyncio
import uuid

import pytest

from app.helpers.unsubscribe import address_hash
from app.services import suppression
from app.storage import bulk_recipients, suppressed


@pytest.fixture
def suppressing(monkeypatch):
    state = {"added": [], "complained": []}

    async def add(address, reason):
        state["added"].append((address, reason))

    async def mark_complained(send_id, user_id):
        state["complained"].append((str(send_id), user_id))

    monkeypatch.setattr(suppressed, "add", add)
    monkeypatch.setattr(bulk_recipients, "mark_complained", mark_complained)

    return state


def test_a_bounce_or_complaint_suppresses_a_members_address(suppressing):
    send = str(uuid.uuid4())
    complaint = {
        "type": "email.complained",
        "data": {"to": ["Ann@Example.com"], "tags": {"kind": "updates", "id": "ann", "send": send}},
    }
    bounce = {"type": "email.bounced", "data": {"to": ["bob@example.com"], "tags": {}}}
    resends = {"type": "email.suppressed", "data": {"to": ["cy@example.com"], "tags": {}}}

    asyncio.run(suppression.from_webhook(complaint))
    asyncio.run(suppression.from_webhook(bounce))
    asyncio.run(suppression.from_webhook(resends))

    assert suppressing["added"] == [
        (address_hash("ann@example.com"), "complained"),
        (address_hash("bob@example.com"), "bounced"),
        (address_hash("cy@example.com"), "suppressed"),
    ]
    assert suppressing["complained"] == [(send, "ann")]


def test_a_candidates_invite_or_another_event_suppresses_nothing(suppressing):
    invite = {
        "type": "email.bounced",
        "data": {"to": ["cat@example.com"], "tags": {"kind": "candidate_invite", "id": "i"}},
    }
    delivered = {"type": "email.delivered", "data": {"to": ["cat@example.com"]}}

    asyncio.run(suppression.from_webhook(invite))
    asyncio.run(suppression.from_webhook(delivered))

    assert suppressing["added"] == []
