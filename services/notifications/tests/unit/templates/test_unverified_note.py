import pytest

from notifications.helpers.emails import candidate_invite_email, candidate_reminder_email

DATA = {"email": "bob@example.com", "token": "xyz", "title": "Backend", "company": "Acme"}


@pytest.mark.parametrize("email", [candidate_invite_email, candidate_reminder_email])
def test_an_invite_from_an_unverified_company_says_so_quietly(email):
    note = "testee hasn't verified Acme."

    unverified = email({**DATA, "verified": False}, "http://localhost:8090", "secret")
    verified = email({**DATA, "verified": True}, "http://localhost:8090", "secret")
    # Events from before invites said: nothing.
    older = email(DATA, "http://localhost:8090", "secret")

    assert note in unverified.text and note in unverified.html
    assert note not in verified.text and note not in older.text
