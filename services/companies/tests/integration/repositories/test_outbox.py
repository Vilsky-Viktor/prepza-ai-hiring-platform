import uuid
from datetime import UTC, datetime, timedelta

from prepza_common.config.constants import OUTBOX_KEEP_DAYS, OUTBOX_MAX_ATTEMPTS
from prepza_common.events import outbox
from sqlalchemy import select

from companies.core.db import Session
from companies.models.outbox import OutboxEvent
from companies.repositories import companies, interviews, invites


def test_a_candidate_invite_and_its_email_event_are_saved_together(run):
    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        # A Russian interview: its invite email goes out in Russian.
        interview = await interviews.create(company.id, uuid.uuid4(), "ru", 60)
        invite, _ = await invites.upsert(
            interview.id, "erin@example.com", "Backend", "Acme", interview.language
        )

        async with Session() as session:
            events = list(
                await session.scalars(
                    select(OutboxEvent).where(OutboxEvent.event_type == "candidate.invited")
                )
            )

        return company, invite, [event.data for event in events]

    company, invite, events = run(scenario())

    assert {
        "invite_id": str(invite.id),
        "company_id": str(company.id),
        "email": "erin@example.com",
        "token": invite.token,
        "title": "Backend",
        "company": "Acme",
        "language": "ru",
        # No logo set: the email shows none.
        "logo_path": None,
        # Not verified: the email says so, quietly.
        "verified": False,
    } in events


def test_a_deleted_company_and_its_company_deleted_event_are_saved_together(run):
    async def scenario():
        company = await companies.create(f"Gone {uuid.uuid4()}", "owner", "owner@example.com")
        await companies.delete(company.id)

        async with Session() as session:
            events = list(
                await session.scalars(
                    select(OutboxEvent.data).where(OutboxEvent.event_type == "company.deleted")
                )
            )

        return company, events

    company, events = run(scenario())

    # Notifications removes the company's notifications when it gets it (retried until then).
    assert {"company_id": str(company.id)} in events


def test_an_invite_without_a_sign_in_is_a_guests_keeps_its_return_address_and_sends_no_email(run):
    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await interviews.create(company.id, uuid.uuid4(), "en", 60)
        invite, _ = await invites.upsert(
            interview.id,
            "quiet@example.com",
            "Backend",
            "Acme",
            "en",
            return_url="https://acme.com/done",
            sign_in=False,
            theme="dark",
        )

        async with Session() as session:
            events = list(
                await session.scalars(
                    select(OutboxEvent).where(OutboxEvent.event_type == "candidate.invited")
                )
            )

        return invite, [event.data["invite_id"] for event in events]

    invite, sent = run(scenario())

    assert str(invite.id) not in sent
    assert invite.return_url == "https://acme.com/done"
    assert invite.guest is True
    assert invite.theme == "dark"
    # No reminder either: the platform that sent the candidate told them already.
    assert invite.reminded_at is not None


def test_old_published_and_parked_events_are_deleted_and_waiting_ones_kept(run):
    async def scenario():
        old = datetime.now(UTC) - timedelta(days=OUTBOX_KEEP_DAYS + 1)
        recent = datetime.now(UTC) - timedelta(days=OUTBOX_KEEP_DAYS - 1)
        rows = {
            "old published": {"created_at": old, "published_at": old},
            "old parked": {"created_at": old, "attempts": OUTBOX_MAX_ATTEMPTS},
            "recent parked": {"created_at": recent, "attempts": OUTBOX_MAX_ATTEMPTS},
            # Still tried by every flush (e.g. during an outage): never dropped unsent.
            "old waiting": {"created_at": old, "attempts": OUTBOX_MAX_ATTEMPTS - 1},
            "recent published": {"created_at": recent, "published_at": recent},
        }

        async with Session() as session:
            for name, columns in rows.items():
                session.add(OutboxEvent(event_type="test.event", data={"name": name}, **columns))

            await session.commit()

        await outbox.delete_old(Session, OutboxEvent)

        async with Session() as session:
            kept = await session.scalars(
                select(OutboxEvent.data["name"].astext).where(
                    OutboxEvent.event_type == "test.event"
                )
            )

            return set(kept)

    assert run(scenario()) == {"recent parked", "old waiting", "recent published"}
