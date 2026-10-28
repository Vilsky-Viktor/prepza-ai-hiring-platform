import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from companies.constants.invites import INVITE_EXPIRY_DAYS, InviteStatus
from companies.integrations import billing
from companies.repositories import interviews, invite_expiry, invites
from companies.services import candidate_billing
from tests.unit.services import test_candidate_billing
from tests.unit.services.test_candidate_billing import COMPANY_ID, INTERVIEW_ID

# What billing was asked to charge, release or hold (test_candidate_billing).
ledger = test_candidate_billing.ledger


def test_invites_never_started_expire_and_give_their_credits_back(ledger, monkeypatch):
    stale = SimpleNamespace(
        id=uuid.uuid4(),
        interview_id=INTERVIEW_ID,
        email="dave@example.com",
        hold_key=f"{INTERVIEW_ID}:dave-key",
    )
    waiting = [stale]
    asked = []

    async def fake_expiring(before, limit):
        asked.append(before)

        return list(waiting)

    async def fake_mark(invite_id, before):
        # Released first, then marked: a release that fails leaves it for the next run.
        assert ledger == [("release", f"{INTERVIEW_ID}:dave-key")]
        waiting.clear()

        return True

    monkeypatch.setattr(invite_expiry, "expiring", fake_expiring)
    monkeypatch.setattr(invite_expiry, "mark_expired", fake_mark)

    assert asyncio.run(candidate_billing.expire_unstarted()) == 1
    expected = datetime.now(UTC) - timedelta(days=INVITE_EXPIRY_DAYS)
    assert abs((asked[0] - expected).total_seconds()) < 5
    assert ledger == [("release", f"{INTERVIEW_ID}:dave-key")]


def test_an_invite_started_or_sent_again_while_expiring_keeps_its_credits(ledger, monkeypatch):
    revived = SimpleNamespace(
        id=uuid.uuid4(),
        interview_id=INTERVIEW_ID,
        email="eve@example.com",
        hold_key=f"{INTERVIEW_ID}:eve-key",
    )
    waiting = [revived]

    async def fake_expiring(before, limit):
        return list(waiting)

    async def not_marked(invite_id, before):
        waiting.clear()

        return False

    async def fake_interview(interview_id):
        return SimpleNamespace(id=interview_id, company_id=COMPANY_ID)

    async def hold(company_id, key):
        ledger.append(("hold", key))

    async def sent_again(invite_id):
        return SimpleNamespace(id=invite_id, status=InviteStatus.INVITED)

    monkeypatch.setattr(invite_expiry, "expiring", fake_expiring)
    monkeypatch.setattr(invite_expiry, "mark_expired", not_marked)
    monkeypatch.setattr(invites, "get", sent_again)
    monkeypatch.setattr(interviews, "get", fake_interview)
    monkeypatch.setattr(billing, "hold_candidate", hold)

    asyncio.run(candidate_billing.expire_unstarted())

    assert ledger == [
        ("release", f"{INTERVIEW_ID}:eve-key"),
        ("hold", f"{INTERVIEW_ID}:eve-key"),
    ]


def test_an_invite_another_run_expired_meanwhile_keeps_nothing_set_aside(ledger, monkeypatch):
    stale = SimpleNamespace(
        id=uuid.uuid4(),
        interview_id=INTERVIEW_ID,
        email="fay@example.com",
        hold_key=f"{INTERVIEW_ID}:fay-key",
    )
    waiting = [stale]

    async def fake_expiring(before, limit):
        return list(waiting)

    async def not_marked(invite_id, before):
        waiting.clear()

        return False

    async def expired(invite_id):
        return SimpleNamespace(id=invite_id, status=InviteStatus.EXPIRED)

    async def hold(company_id, key):
        ledger.append(("hold", key))

    monkeypatch.setattr(invite_expiry, "expiring", fake_expiring)
    monkeypatch.setattr(invite_expiry, "mark_expired", not_marked)
    monkeypatch.setattr(invites, "get", expired)
    monkeypatch.setattr(billing, "hold_candidate", hold)

    asyncio.run(candidate_billing.expire_unstarted())

    # A retried schedule overlapping the first run: its release is the only movement.
    assert ledger == [("release", f"{INTERVIEW_ID}:fay-key")]


def test_a_leaving_candidate_frees_only_unfinished_invites(ledger):
    asyncio.run(
        candidate_billing.release_unfinished(
            [
                (INTERVIEW_ID, "a@example.com", InviteStatus.INVITED, f"{INTERVIEW_ID}:a-key"),
                (INTERVIEW_ID, "b@example.com", InviteStatus.IN_PROCESS, f"{INTERVIEW_ID}:b-key"),
                (INTERVIEW_ID, "c@example.com", InviteStatus.FINISHED, f"{INTERVIEW_ID}:c-key"),
            ]
        )
    )

    assert ledger == [
        ("release", f"{INTERVIEW_ID}:a-key"),
        ("release", f"{INTERVIEW_ID}:b-key"),
    ]
