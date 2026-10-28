import pytest

from notifications.helpers.emails import candidate_joined_email
from notifications.integrations import smtp
from notifications.repositories import opt_outs
from notifications.services import events
from tests.unit.handlers.test_events import push

DATA = {
    "invite_id": "inv-1",
    "company_id": "c-1",
    "email": "bob@example.com",
    "token": "xyz",
    "title": "Backend",
    "company": "Acme",
}


@pytest.fixture
def sent(monkeypatch):
    """The addresses emailed; Bob hasn't stopped Acme's emails unless a test says so."""
    to = []

    async def send(email):
        to.append(email.to)

    async def not_opted_out(address, company_id, invite_id=None):
        return False

    monkeypatch.setattr(smtp, "send", send)
    monkeypatch.setattr(opt_outs, "opted_out", not_opted_out)

    return to


def test_someone_who_started_through_a_link_gets_their_own_link_to_continue():
    email = candidate_joined_email(DATA, "http://localhost:8090", "secret")

    assert email.to == "bob@example.com"
    assert "Backend" in email.subject
    assert 'href="http://localhost:8090/invite/xyz"' in email.html
    assert "You started the “Backend” interview for Acme on prepza." in email.text
    assert "Don't email me for Acme" in email.text
    # A bounce leaves the invite as it is: they're already taking the test.
    assert email.tags == {}


def test_a_joined_event_sends_its_email(client, sent):
    assert client.post("/internal/events", json=push("candidate.joined", DATA)).status_code == 204
    assert sent == ["bob@example.com"]


def test_no_email_to_someone_who_stopped_the_companys_emails(client, sent, monkeypatch):
    async def opted_out(address, company_id, invite_id=None):
        return True

    monkeypatch.setattr(events.opt_outs, "opted_out", opted_out)

    assert client.post("/internal/events", json=push("candidate.joined", DATA)).status_code == 204
    assert sent == []
