import pytest

from companies.constants.invites import ALREADY_FINISHED, INTERVIEW_NOT_READY, InviteStatus
from companies.helpers.candidates import row_actions
from companies.integrations import billing
from companies.main import app
from companies.repositories import invites
from companies.services import candidate_invites
from tests.unit.api.v1.test_candidate_invites import URL, invite_setup


def test_a_finished_candidate_is_not_invited_again(client, monkeypatch):
    sent, used = invite_setup(monkeypatch)

    async def finished(_interview_id, _email):
        return InviteStatus.FINISHED, "key"

    monkeypatch.setattr(invites, "held", finished)

    response = client.post(URL, json={"email": "carol@example.com"})
    app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json() == {"detail": ALREADY_FINISHED, "code": "candidate_finished"}
    assert sent == used == []


@pytest.mark.parametrize(
    ("status", "can_resend", "revokable"),
    [
        (InviteStatus.INVITED, True, True),
        (InviteStatus.EXPIRED, True, True),
        (InviteStatus.IN_PROCESS, True, False),
        (InviteStatus.FINISHED, False, False),
        (InviteStatus.DELETED, False, False),
    ],
)
def test_the_server_says_what_each_candidate_allows(status, can_resend, revokable):
    assert row_actions(status) == {"can_resend": can_resend, "revokable": revokable}


def test_an_interview_without_its_title_sends_no_invite_and_keeps_no_credits(client, monkeypatch):
    sent, used = invite_setup(monkeypatch)
    released = []

    async def no_title(interview):
        return None

    async def release(key):
        released.append(key)

    counted = []

    async def count(*args):
        counted.append(args)

    monkeypatch.setattr(candidate_invites, "interview_title", no_title)
    monkeypatch.setattr(candidate_invites, "hit_emails", count)
    monkeypatch.setattr(billing, "release_candidate", release)

    response = client.post(URL, json={"email": "carol@example.com"})
    app.dependency_overrides.clear()

    assert (response.status_code, response.json()["detail"]) == (409, INTERVIEW_NOT_READY)
    assert response.json()["code"] == "interview_not_ready"
    assert sent == [] and released == used
    # No email went, so none counts against the email limits.
    assert counted == []
