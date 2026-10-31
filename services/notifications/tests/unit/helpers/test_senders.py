import pytest

from notifications.config import settings
from notifications.helpers.emails import (
    candidate_invite_email,
    candidate_joined_email,
    candidate_reminder_email,
    member_invite_email,
)
from notifications.helpers.senders import sender
from notifications.models.email import Email

INVITE = {
    "email": "ann@example.com",
    "token": "t",
    "title": "Backend",
    "company": "Acme",
    "company_id": "c-1",
    "invite_id": "i-1",
}
SITE = "https://testee.ai"


@pytest.fixture
def senders(monkeypatch):
    monkeypatch.setattr(settings, "mail_from", "service@testee.ai")
    monkeypatch.setattr(settings, "mail_from_updates", "updates@mail.testee.ai")
    monkeypatch.setattr(settings, "mail_from_candidates", "")


@pytest.mark.parametrize(
    "build", [candidate_invite_email, candidate_joined_email, candidate_reminder_email]
)
def test_candidates_emails_come_from_their_own_sender_once_one_is_set(senders, monkeypatch, build):
    email = build(INVITE, SITE, "secret")

    assert sender(email) == "service@testee.ai"

    monkeypatch.setattr(settings, "mail_from_candidates", "invites@candidates.testee.ai")

    assert sender(email) == "invites@candidates.testee.ai"


def test_other_emails_keep_their_senders(senders, monkeypatch):
    monkeypatch.setattr(settings, "mail_from_candidates", "invites@candidates.testee.ai")
    team = member_invite_email({**INVITE, "role": "admin", "inviter": "Bob"}, SITE)
    optional = Email(to="a@example.com", subject="s", html="h", text="t", optional=True)

    assert (sender(team), sender(optional)) == ("service@testee.ai", "updates@mail.testee.ai")
