import pytest

from app.config.settings import settings
from app.helpers.emails import (
    candidate_invite_email,
    candidate_joined_email,
    candidate_reminder_email,
    member_invite_email,
)
from app.helpers.senders import sender
from app.models.email import Email

INVITE = {
    "email": "ann@example.com",
    "token": "t",
    "title": "Backend",
    "company": "Acme",
    "company_id": "c-1",
    "invite_id": "i-1",
}
SITE = "https://prepza.ai"


@pytest.fixture
def senders(monkeypatch):
    monkeypatch.setattr(settings, "mail_from", "service@prepza.ai")
    monkeypatch.setattr(settings, "mail_from_updates", "updates@mail.prepza.ai")
    monkeypatch.setattr(settings, "mail_from_candidates", "")


@pytest.mark.parametrize(
    "build", [candidate_invite_email, candidate_joined_email, candidate_reminder_email]
)
def test_candidates_emails_come_from_their_own_sender_once_one_is_set(senders, monkeypatch, build):
    email = build(INVITE, SITE, "secret")

    assert sender(email) == "service@prepza.ai"

    monkeypatch.setattr(settings, "mail_from_candidates", "invites@candidates.prepza.ai")

    assert sender(email) == "invites@candidates.prepza.ai"


def test_other_emails_keep_their_senders(senders, monkeypatch):
    monkeypatch.setattr(settings, "mail_from_candidates", "invites@candidates.prepza.ai")
    team = member_invite_email({**INVITE, "role": "admin", "inviter": "Bob"}, SITE)
    optional = Email(to="a@example.com", subject="s", html="h", text="t", optional=True)

    assert (sender(team), sender(optional)) == ("service@prepza.ai", "updates@mail.prepza.ai")
