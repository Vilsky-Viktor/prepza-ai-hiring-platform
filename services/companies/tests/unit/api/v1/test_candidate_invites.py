import re
import uuid
from datetime import UTC, datetime

from fake_redis import FakeRedis
from fastapi import HTTPException
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User
from prepza_common.events.audit_actions import AuditAction, TargetKind

from companies.integrations import billing
from companies.main import app
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import companies, interviews, invites
from companies.services import candidate_invites
from companies.services import outbox as outbox_service

COMPANY_ID = uuid.uuid4()
INTERVIEW_ID = uuid.uuid4()


def invite_setup(monkeypatch):
    """Signs in Bob, Acme's owner; returns the emails the published events would send."""
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True, name="Bob"
    )
    interview = Interview(
        id=INTERVIEW_ID,
        company_id=COMPANY_ID,
        generation_id=uuid.uuid4(),
        set_id=uuid.uuid4(),
        title="Backend interview",
    )
    company = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC))
    company.members = [
        Member(company_id=COMPANY_ID, user_id="bob", invited_email="bob@example.com", role="owner")
    ]
    invite = CandidateInvite(
        id=uuid.uuid4(),
        interview_id=INTERVIEW_ID,
        email="carol@example.com",
        token="token",
        status="invited",
        created_at=datetime.now(UTC),
    )
    sent = []
    invited = set()
    used = []

    async def fake_interview(_interview_id):
        return interview

    async def fake_company(_company_id):
        return company

    async def fake_upsert(
        _interview_id,
        email,
        title,
        company,
        language,
        logo_path=None,
        hold_key=None,
        name=None,
        verified=False,
        return_url=None,
        sign_in=True,
        theme=None,
    ):
        # A new invite keeps the key its credits were set aside under.
        invite.hold_key = invite.hold_key or hold_key
        # The storage saves the email's event in the invite's transaction.
        sent.append(email)
        invited.add(email)

        return invite, False

    async def fake_status(_interview_id, email):
        return (await fake_held(_interview_id, email))[0]

    async def fake_held(_interview_id, email):
        return ("invited", invite.hold_key) if email in invited else (None, None)

    async def fake_statuses(_interview_id, emails):
        return {email: "invited" for email in emails if email in invited}

    async def fake_hold(company_id, key):
        # Billing sets credits aside once per key, however often it's asked.
        if key not in used:
            used.append(key)

    async def no_flush():
        pass

    monkeypatch.setattr(interviews, "get", fake_interview)
    monkeypatch.setattr(companies, "get", fake_company)
    monkeypatch.setattr(invites, "upsert", fake_upsert)
    monkeypatch.setattr(invites, "held", fake_held)
    monkeypatch.setattr(invites, "status_of", fake_status)
    monkeypatch.setattr(invites, "statuses_of", fake_statuses)
    monkeypatch.setattr(billing, "hold_candidate", fake_hold)
    monkeypatch.setattr(outbox_service, "flush_quietly", no_flush)
    redis = FakeRedis()
    monkeypatch.setattr(candidate_invites, "get_redis", lambda: redis)

    return sent, used


URL = f"/interviews/{INTERVIEW_ID}/candidates"


def test_inviting_the_same_email_again_resends_the_invite(client, monkeypatch, audited):
    sent, used = invite_setup(monkeypatch)
    url = URL

    first = client.post(url, json={"email": "Carol@example.com"})
    second = client.post(url, json={"email": "carol@example.com"})

    # Sent again while still open: nothing new was made.
    assert (first.status_code, second.status_code) == (201, 200)
    # Credits are set aside once for the candidate; the resend costs nothing more.
    # Set aside once, under the invite's own key.
    assert len(used) == 1
    # A new key of its own, without the candidate's email.
    assert re.fullmatch(rf"{INTERVIEW_ID}:[0-9a-f]{{32}}", used[0])
    assert first.json()["id"] == second.json()["id"]
    assert sent == ["carol@example.com", "carol@example.com"]
    invite_id = uuid.UUID(first.json()["id"])
    assert [event[2:] for event in audited] == [
        (AuditAction.CANDIDATE_INVITED, invite_id, TargetKind.CANDIDATE),
        (AuditAction.INVITE_RESENT, invite_id, TargetKind.CANDIDATE),
    ]

    app.dependency_overrides.clear()


def test_one_address_gets_at_most_three_invites_a_day(client, monkeypatch):
    sent, _ = invite_setup(monkeypatch)

    codes = [client.post(URL, json={"email": "carol@example.com"}).status_code for _ in range(4)]
    other = client.post(URL, json={"email": "dave@example.com"})
    app.dependency_overrides.clear()

    assert codes == [201, 200, 200, 429]
    assert other.status_code == 201
    assert len(sent) == 4


def test_a_company_without_credits_cannot_invite_new_candidates(client, monkeypatch):
    sent, _ = invite_setup(monkeypatch)

    async def no_credits(company_id, key):
        raise HTTPException(402, "No candidate credits left.")

    monkeypatch.setattr(billing, "hold_candidate", no_credits)

    response = client.post(URL, json={"email": "erin@example.com"})
    app.dependency_overrides.clear()

    assert response.status_code == 402
    assert response.json()["detail"] == "No candidate credits left."
    assert sent == []


def test_invites_refused_for_credits_use_up_no_email_limits(client, monkeypatch):
    """Otherwise a company out of credits (an ATS sending candidates) would use up the limits,
    and invites would be refused with 429 once it tops up."""
    sent, _ = invite_setup(monkeypatch)
    hold = billing.hold_candidate

    async def no_credits(company_id, key):
        raise HTTPException(402, "No candidate credits left.")

    monkeypatch.setattr(billing, "hold_candidate", no_credits)
    refused = [client.post(URL, json={"email": "erin@example.com"}).status_code for _ in range(4)]
    monkeypatch.setattr(billing, "hold_candidate", hold)
    codes = [client.post(URL, json={"email": "erin@example.com"}).status_code for _ in range(3)]
    app.dependency_overrides.clear()

    assert refused == [402] * 4
    assert codes == [201, 200, 200]
    assert len(sent) == 3


def limited_setup(monkeypatch, current):
    """An invite in `current` status refused over the email limits; returns the credits held
    and released."""
    _, used = invite_setup(monkeypatch)
    released = []

    async def limited(*args):
        raise HTTPException(429, "Too many requests. Try again later.")

    async def fake_held(_interview_id, email):
        return current, "stored-key" if current else None

    async def fake_status(_interview_id, email):
        return current

    async def fake_release(key):
        released.append(key)

    monkeypatch.setattr(candidate_invites, "hit_emails", limited)
    monkeypatch.setattr(invites, "held", fake_held)
    monkeypatch.setattr(invites, "status_of", fake_status)
    monkeypatch.setattr(billing, "release_candidate", fake_release)

    return used, released


def test_a_new_invite_refused_over_the_email_limits_gives_its_credits_back(client, monkeypatch):
    used, released = limited_setup(monkeypatch, None)

    response = client.post(URL, json={"email": "frank@example.com"})
    app.dependency_overrides.clear()

    assert response.status_code == 429
    assert len(used) == 1
    assert released == used


def test_an_expired_invite_refused_over_the_email_limits_gives_its_credits_back(
    client, monkeypatch
):
    used, released = limited_setup(monkeypatch, "expired")

    response = client.post(URL, json={"email": "frank@example.com"})
    app.dependency_overrides.clear()

    assert response.status_code == 429
    assert used == released == ["stored-key"]


def test_an_expired_invite_sent_again_meanwhile_keeps_its_credits(client, monkeypatch):
    """Another request revived it between the read and the refusal: its credits stay held."""
    _, released = limited_setup(monkeypatch, "expired")
    holds = []

    async def fake_status(_interview_id, email):
        return "invited"

    async def fake_hold(company_id, key):
        holds.append(key)

    monkeypatch.setattr(invites, "status_of", fake_status)
    monkeypatch.setattr(billing, "hold_candidate", fake_hold)

    response = client.post(URL, json={"email": "frank@example.com"})
    app.dependency_overrides.clear()

    assert response.status_code == 429
    assert released == ["stored-key"]
    assert holds == ["stored-key", "stored-key"]


def test_an_invited_candidate_refused_over_the_email_limits_keeps_their_credits(
    client, monkeypatch
):
    _, released = limited_setup(monkeypatch, "invited")

    response = client.post(URL, json={"email": "frank@example.com"})
    app.dependency_overrides.clear()

    assert response.status_code == 429
    assert released == []


def test_an_invite_that_expired_while_sent_again_has_its_credits_set_aside_again(
    client, monkeypatch
):
    """Expiry gave them back after the invite was read; otherwise it finishes uncharged."""
    _, used = invite_setup(monkeypatch)
    upsert = invites.upsert
    held = []

    async def revived(*args, **kwargs):
        invite, _ = await upsert(*args, **kwargs)

        return invite, True

    async def hold_again(invite, key):
        held.append(key)

    monkeypatch.setattr(invites, "upsert", revived)
    monkeypatch.setattr(candidate_invites, "hold_again", hold_again)

    response = client.post(URL, json={"email": "gina@example.com"})
    app.dependency_overrides.clear()

    assert response.status_code == 201
    assert held == used
