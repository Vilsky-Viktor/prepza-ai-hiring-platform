import asyncio
import json
import uuid
from datetime import UTC, date, datetime, timedelta

import httpx
import pytest
from prepza_common import http
from prepza_common.notifications import NotificationKind, Recipient, notification

from app.config.settings import settings
from app.constants.member_emails import DIGEST_HOUR
from app.integrations import smtp
from app.services import digest, reminders
from app.storage import notifications, sent_emails
from tests.integration.factories import api

TODAY = date(2026, 10, 8)


def user() -> str:
    """A user of their own for each test: the database is shared by the whole run."""
    return f"u-{uuid.uuid4()}"


def test_a_claim_is_taken_once_even_by_two_runs_at_once(run):
    ann = user()

    async def scenario():
        both = await asyncio.gather(*[sent_emails.claim(ann, "digest", TODAY, 1) for _ in range(5)])
        tomorrow = await sent_emails.claim(ann, "digest", TODAY + timedelta(days=1), 1)

        return both, tomorrow

    both, tomorrow = run(scenario())

    assert sorted(both, key=lambda found: found is None) == [[], None, None, None, None]
    assert tomorrow == []


def test_a_reminder_waits_a_week_and_never_names_the_same_thing_twice(run):
    ann = user()

    async def scenario():
        first = await sent_emails.claim(ann, "no_candidates", TODAY, 7, ["i1"])
        same_week = await sent_emails.claim(
            ann, "no_candidates", TODAY + timedelta(days=6), 7, ["i2"]
        )
        again = await sent_emails.claim(ann, "no_candidates", TODAY + timedelta(days=7), 7, ["i1"])
        new = await sent_emails.claim(
            ann, "no_candidates", TODAY + timedelta(days=7), 7, ["i1", "i2"]
        )

        return first, same_week, again, new

    assert run(scenario()) == (["i1"], None, None, ["i2"])


def test_a_released_claim_is_sent_by_the_next_run(run):
    ann = user()

    async def scenario():
        await sent_emails.claim(ann, "no_candidates", TODAY, 7, ["i1"])
        await sent_emails.release(ann, "no_candidates", TODAY, ["i1"])

        return await sent_emails.claim(ann, "no_candidates", TODAY, 7, ["i1"])

    assert run(scenario()) == ["i1"]


@pytest.fixture
def outside(monkeypatch):
    """Companies, library, billing and generation answer; SMTP records what's sent."""
    state = {"sent": [], "people": []}
    company_id = str(uuid.uuid4())

    def answer(request: httpx.Request) -> httpx.Response:
        path = request.url.path

        if path == "/internal/companies/members":
            ids = json.loads(request.content)["company_ids"]
            members = [{"user_id": found["user_id"], "editor": True} for found in state["people"]]

            return httpx.Response(
                200,
                json={
                    "companies": [{"id": company_id, "name": "Acme", "members": members}]
                    if company_id in ids
                    else []
                },
            )

        if path == "/internal/users/email-recipients":
            return httpx.Response(200, json={"recipients": state["people"]})

        if path == "/internal/companies/low":
            return httpx.Response(
                200, json={"companies": [{"company_id": company_id, "available": 50}]}
            )

        if path == "/internal/interviews/waiting":
            return httpx.Response(200, json={"without_candidates": [], "being_generated": []})

        return httpx.Response(404)

    async def send(email):
        state["sent"].append(email)

    async def no_wait(seconds):
        return None

    monkeypatch.setattr(settings, "resend_api_key", "")
    monkeypatch.setattr(smtp, "send", send)
    monkeypatch.setattr("app.services.member_sends.asyncio.sleep", no_wait)
    monkeypatch.setattr(
        http, "get_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(answer))
    )
    state["company_id"] = company_id

    return state


def person(user_id: str, **preferences) -> dict:
    on = dict.fromkeys(
        [
            "candidate_finished",
            "invite_undelivered",
            "ats_not_invited",
            "interview_ready",
            "reminders",
        ],
        True,
    )

    return {
        "user_id": user_id,
        "email": f"{user_id}@example.com",
        "language": "de",
        "preferences": {**on, **preferences},
    }


def test_the_digest_tells_yesterdays_activity_once_in_the_users_language(run, outside):
    ann, bob = user(), user()
    outside["people"] = [person(ann), person(bob, candidate_finished=False)]
    now = datetime.now(UTC)
    event = notification(
        Recipient.COMPANY,
        outside["company_id"],
        NotificationKind.CANDIDATE_FINISHED,
        "/companies/x/interviews/y",
        title="Backend",
    )

    async def scenario():
        await notifications.add(str(uuid.uuid4()), event)
        # The run at the next DIGEST_HOUR covers it, whatever the time now; a second run that
        # hour sends nothing more.
        later = now if now.hour < DIGEST_HOUR else now + timedelta(days=1)
        first = await digest.send_digests(later)
        second = await digest.send_digests(later)

        return first, second

    first, second = run(scenario())

    assert (first, second) == (1, 0)
    [email] = outside["sent"]
    assert email.to == f"{ann}@example.com"
    assert email.subject == "Deine Aktivitätsübersicht auf prepza"
    assert "List-Unsubscribe" in email.headers


def test_reminders_are_sent_once_a_week_and_not_to_those_who_turned_them_off(run, outside):
    ann, bob = user(), user()
    outside["people"] = [person(ann), person(bob, reminders=False)]
    now = datetime.now(UTC)

    async def scenario():
        first = await reminders.send_reminders(now)
        again = await reminders.send_reminders(now + timedelta(days=1))

        return first, again

    assert run(scenario()) == (1, 0)
    assert [email.to for email in outside["sent"]] == [f"{ann}@example.com"]


def test_the_schedules_answer_204(run, outside):
    async def scenario():
        async with api() as client:
            return [
                (await client.post(f"/internal/schedules/{name}")).status_code
                for name in ("digest", "reminders")
            ]

    assert run(scenario()) == [204, 204]
