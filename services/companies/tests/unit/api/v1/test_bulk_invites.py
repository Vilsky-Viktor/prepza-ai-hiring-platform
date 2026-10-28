from fastapi import HTTPException

from companies.api.v1 import bulk_invites
from companies.helpers.email_lists import emails_in
from companies.integrations import billing
from companies.repositories import invites
from companies.services import candidate_invites
from tests.unit.api.v1.test_candidate_invites import INTERVIEW_ID, invite_setup

URL = f"/interviews/{INTERVIEW_ID}/candidates/bulk"


def test_emails_are_found_in_any_list_once_each_in_order():
    text = "Name,Email\nAnn Lee,Ann@Example.com\nBob <bob@example.com>; ann@example.com."

    assert emails_in(text) == ["ann@example.com", "bob@example.com"]


def test_every_email_in_the_list_is_invited_and_bad_ones_are_said_why(client, monkeypatch):
    sent, _ = invite_setup(monkeypatch)

    response = client.post(URL, json={"text": "ann@example.com\nbad@@example\nbob@example.com"})

    assert response.status_code == 200
    assert response.json() == {
        "invited": ["ann@example.com", "bob@example.com"],
        "skipped": [],
        "problems": [{"line": "bad@@example", "reason": "invalid_email"}],
    }
    assert sent == ["ann@example.com", "bob@example.com"]


def test_out_of_credits_stops_the_rest_of_the_list(client, monkeypatch):
    invite_setup(monkeypatch)
    held = []

    async def one_credit(company_id, key):
        if held:
            raise HTTPException(402, "Out of credits")

        held.append(key)

    monkeypatch.setattr(billing, "hold_candidate", one_credit)

    result = client.post(URL, json={"text": "a@example.com b@example.com c@example.com"}).json()

    assert result["invited"] == ["a@example.com"]
    assert [(row["email"], row["reason"]) for row in result["skipped"]] == [
        ("b@example.com", "no_credits"),
        ("c@example.com", "no_credits"),
    ]


def test_email_limits_skip_an_email_but_not_the_list(client, monkeypatch):
    invite_setup(monkeypatch)

    async def limited(redis, sender, recipient, *limits):
        if recipient.endswith("a@example.com"):
            raise HTTPException(429, "Too many emails")

    monkeypatch.setattr(candidate_invites, "hit_emails", limited)

    result = client.post(URL, json={"text": "a@example.com b@example.com"}).json()

    assert result["invited"] == ["b@example.com"]
    assert result["skipped"] == [{"email": "a@example.com", "reason": "limit"}]


def test_a_list_without_emails_or_with_too_many_is_refused(client, monkeypatch):
    invite_setup(monkeypatch)
    many = " ".join(f"c{number}@example.com" for number in range(101))

    # Only blank lines: nothing to read. (Lines without an email are reported, not refused.)
    assert client.post(URL, json={"text": " \n "}).status_code == 422
    assert client.post(URL, json={"text": many}).status_code == 422


def test_a_candidate_who_already_started_is_skipped_not_emailed_again(client, monkeypatch):
    sent, _ = invite_setup(monkeypatch)

    async def started(session, _interview_id, emails):
        return {email: "in_process" for email in emails if email == "ann@example.com"}

    monkeypatch.setattr(invites, "statuses_of", started)

    result = client.post(URL, json={"text": "Ann@example.com bob@example.com"}).json()

    assert result["invited"] == ["bob@example.com"]
    assert result["skipped"] == [{"email": "ann@example.com", "reason": "started"}]
    assert sent == ["bob@example.com"]


def test_a_list_is_read_off_the_event_loop(client, monkeypatch):
    invite_setup(monkeypatch)
    threads = []
    run_in_thread = bulk_invites.asyncio.to_thread

    async def to_thread(function, *args):
        threads.append(function.__name__)

        return await run_in_thread(function, *args)

    monkeypatch.setattr(bulk_invites.asyncio, "to_thread", to_thread)

    assert client.post(URL, json={"text": "ann@example.com"}).status_code == 200
    assert "read_list" in threads
