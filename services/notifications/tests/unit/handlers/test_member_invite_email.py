import pytest
from fastapi.testclient import TestClient
from prepza_common.config.constants import LANGUAGES

from notifications.helpers.emails import member_invite_email
from notifications.integrations import smtp
from notifications.main import app
from notifications.templates.emails import EMAILS
from tests.unit.handlers.test_events import (  # noqa: F401 (the emulator fixture is autouse)
    emulator,
    push,
)

MEMBER = {
    "email": "dan@example.com",
    "token": "abc",
    "role": "viewer",
    "company": "Acme & Co",
    "company_id": "c-1",
    "inviter": "Ann",
    "language": "en",
    "logo_path": None,
}
# The English subject, filled in.
SUBJECT = EMAILS["en"]["member"]["subject"].format(company="Acme & Co", inviter="Ann")


def test_a_member_invite_names_the_inviter_the_company_and_the_role_and_links_to_join():
    email = member_invite_email(MEMBER, "https://prepza.com/")

    assert email.to == "dan@example.com"
    assert "Acme & Co" in email.subject
    assert "Ann invited you to join Acme & Co on prepza as a viewer." in email.text
    assert "https://prepza.com/join/abc" in email.text
    assert "Acme &amp; Co" in email.html
    assert "<img" not in email.html


def test_a_member_invite_shows_the_companys_logo_beside_the_title():
    email = member_invite_email(
        {**MEMBER, "role": "admin", "logo_path": "/api/companies/companies/c-1/logo?v=2"},
        "https://prepza.com",
    )

    assert "as an admin." in email.text
    title_row = email.html.split("</h1></td>", 1)[1].split("</tr>", 1)[0]
    assert '<img src="https://prepza.com/api/companies/companies/c-1/logo?v=2"' in title_row


@pytest.mark.parametrize("language", sorted(LANGUAGES))
def test_every_language_has_the_member_invite(language):
    for role in ("admin", "viewer"):
        email = member_invite_email({**MEMBER, "role": role, "language": language}, "")

        # Every placeholder is filled in, and the texts aren't English stand-ins.
        assert "{" not in email.html and "{" not in email.text
        assert f'lang="{language}"' in email.html
        assert language == "en" or email.subject != SUBJECT


def test_a_member_invite_event_sends_its_email(client, monkeypatch):
    sent = []

    async def fake_send(email):
        sent.append((email.to, email.subject))

    monkeypatch.setattr(smtp, "send", fake_send)

    assert client.post("/internal/events", json=push("member.invited", MEMBER)).status_code == 204
    assert sent == [("dan@example.com", SUBJECT)]


def test_a_member_invite_event_without_its_sender_is_acknowledged_once_and_sends_nothing(
    client, monkeypatch
):
    """No retry can fill in the sender: the event is acknowledged rather than failing on every
    redelivery."""
    sent = []

    async def fake_send(email):
        sent.append(email.to)

    monkeypatch.setattr(smtp, "send", fake_send)
    unsigned = {key: value for key, value in MEMBER.items() if key != "inviter"}

    assert client.post("/internal/events", json=push("member.invited", unsigned)).status_code == 204
    assert sent == []


def test_a_member_invite_the_mail_server_failed_to_take_is_retried(monkeypatch):
    async def down(email):
        raise ConnectionError("The mail server went away")

    monkeypatch.setattr(smtp, "send", down)
    client = TestClient(app, raise_server_exceptions=False)

    assert client.post("/internal/events", json=push("member.invited", MEMBER)).status_code == 500
