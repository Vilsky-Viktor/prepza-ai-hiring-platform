import httpx
import pytest

from companies.integrations import billing
from companies.main import app
from companies.repositories import invites
from companies.services import candidate_invites
from tests.unit.api.v1.test_candidate_invites import URL, invite_setup


def failing_setup(monkeypatch, current, step):
    """An invite in `current` status whose `step` fails after (or while) its credits are set
    aside; returns the credits held and released."""
    _, used = invite_setup(monkeypatch)
    released = []

    async def fake_held(session, _interview_id, email):
        return current, "stored-key" if current else None

    async def fake_status(session, _interview_id, email):
        return current

    async def fake_release(key):
        released.append(key)

    async def broken(session, *args, **kwargs):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(invites, "held", fake_held)
    monkeypatch.setattr(invites, "status_of", fake_status)
    monkeypatch.setattr(billing, "release_candidate", fake_release)

    if step == "hold":
        # Billing's answer lost on the way: the hold may have been made.
        async def lost(company_id, key):
            used.append(key)

            raise httpx.ReadTimeout("billing took too long")

        monkeypatch.setattr(billing, "hold_candidate", lost)
    elif step == "limits":
        # Redis failing, not a refusal over the limits.
        monkeypatch.setattr(candidate_invites, "hit_emails", broken)
    else:
        monkeypatch.setattr(invites, "upsert", broken)

    return used, released


@pytest.mark.parametrize("step", ["hold", "limits", "save"])
@pytest.mark.parametrize("current", [None, "expired"])
def test_credits_set_aside_for_an_invite_that_failed_come_back(client, monkeypatch, step, current):
    used, released = failing_setup(monkeypatch, current, step)

    with pytest.raises(httpx.HTTPError):
        client.post(URL, json={"email": "frank@example.com"})

    app.dependency_overrides.clear()

    assert len(used) == 1
    assert released == used


def test_an_invited_candidates_credits_stay_when_sending_again_fails(client, monkeypatch):
    _, released = failing_setup(monkeypatch, "invited", "save")

    with pytest.raises(httpx.HTTPError):
        client.post(URL, json={"email": "frank@example.com"})

    app.dependency_overrides.clear()

    assert released == []
