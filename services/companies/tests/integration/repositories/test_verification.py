import uuid

from alembic import command
from alembic.config import Config
from prepza_common.db.db import sqlalchemy_url
from sqlalchemy import create_engine, select, text

from companies.config import settings
from companies.core.db import Session
from companies.models.outbox import OutboxEvent
from companies.repositories import companies, verification
from tests.integration import factories
from tests.integration.transactions import transaction


async def company(name="Acme"):
    return await factories.company(f"{name} {uuid.uuid4()}", "ann", "ann@acme.com")


async def notices(kind):
    query = select(OutboxEvent).where(OutboxEvent.data["kind"].astext == kind)

    async with Session() as session:
        return list(await session.scalars(query))


def test_proof_sends_the_current_name_for_review_and_approval_gives_the_badge(run):
    async def scenario():
        found = await company()
        await transaction(verification.set_website, found.id, "acme.com", None)
        waiting = await transaction(companies.get, found.id)
        await transaction(verification.set_website, found.id, "acme.com", "ann@acme.com")
        pending = await transaction(companies.get, found.id)
        approved = await transaction(
            verification.decide, found.id, True, "root", None, [{"kind": "x"}]
        )
        again = await transaction(verification.decide, found.id, False, "root", "No", [])

        return waiting, pending, approved, again, await transaction(companies.get, found.id)

    waiting, pending, approved, again, decided = run(scenario())

    assert (waiting.verification_status, waiting.verified_domain) == ("waiting_email", None)
    assert pending.verification_status == "pending"
    assert pending.verification_name == pending.name
    assert pending.verification_email == "ann@acme.com"
    assert pending.verification_submitted_at is not None
    assert pending.verified_domain is None
    assert (approved, again) == (True, False)
    assert decided.verification_status == "approved"
    assert decided.verified_domain == "acme.com"
    assert decided.verification_decided_by == "root"


def test_a_decline_keeps_its_reason_and_notifies_in_the_same_transaction(run):
    async def scenario():
        found = await company()
        await transaction(verification.set_website, found.id, "acme.com", "ann@acme.com")
        notice = {"kind": "verification_declined", "recipient_id": str(found.id)}
        await transaction(verification.decide, found.id, False, "root", "Not them", [notice])
        sent = await notices("verification_declined")

        return await transaction(companies.get, found.id), sent, found.id

    declined, sent, company_id = run(scenario())

    assert (declined.verification_status, declined.decline_reason) == ("declined", "Not them")
    assert declined.verified_domain is None
    assert [row.data["recipient_id"] for row in sent].count(str(company_id)) == 1


def test_renaming_takes_the_badge_away_until_the_new_name_is_reviewed(run):
    async def scenario():
        approved = await company()
        await transaction(verification.set_website, approved.id, "acme.com", "ann@acme.com")
        await transaction(verification.decide, approved.id, True, "root", None, [])
        waiting = await company("Waiting")
        await transaction(verification.set_website, waiting.id, "waiting.com", None)
        new_name = f"Renamed {uuid.uuid4()}"
        await factories.renamed(approved.id, new_name)
        await factories.renamed(waiting.id, f"Other {uuid.uuid4()}")

        return (
            await transaction(companies.get, approved.id),
            await transaction(companies.get, waiting.id),
            new_name,
        )

    renamed, still_waiting, new_name = run(scenario())

    assert renamed.verification_status == "pending"
    assert renamed.verified_domain is None
    assert renamed.verification_name == new_name
    assert renamed.verification_email == "ann@acme.com"
    assert renamed.verification_decided_by is None
    assert still_waiting.verification_status == "waiting_email"


def test_the_list_has_pending_first_then_the_latest_decided(run):
    async def scenario():
        ids = []

        for _ in range(3):
            found = await company()
            await transaction(verification.set_website, found.id, "acme.com", "ann@acme.com")
            ids.append(found.id)

        await transaction(verification.decide, ids[0], True, "root", None, [])
        await transaction(verification.decide, ids[1], False, "root", None, [])
        waiting = await company()
        await transaction(verification.set_website, waiting.id, "acme.com", None)
        rows = await transaction(verification.requests, 0, 1000)

        return [row.id for row in rows], ids, waiting.id

    order, ids, waiting = run(scenario())
    mine = [item for item in order if item in ids]

    assert mine == [ids[2], ids[1], ids[0]]
    assert waiting not in order


def test_the_migration_keeps_verified_companies_approved():
    config = Config("alembic.ini")
    engine = create_engine(sqlalchemy_url(settings.database_url))
    verified, waiting = uuid.uuid4(), uuid.uuid4()
    command.downgrade(config, "0026")

    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO companies (id, name, website_domain, verified_domain, "
                    "logo_version, created_at) VALUES "
                    "(:verified, :name1, 'v.com', 'v.com', 0, now()), "
                    "(:waiting, :name2, 'w.com', NULL, 0, now())"
                ),
                {
                    "verified": verified,
                    "waiting": waiting,
                    "name1": f"V {verified}",
                    "name2": f"W {waiting}",
                },
            )
    finally:
        command.upgrade(config, "head")

    with engine.connect() as connection:
        rows = dict(
            connection.execute(
                text("SELECT id, verification_status FROM companies WHERE id IN (:a, :b)"),
                {"a": verified, "b": waiting},
            ).all()
        )

    engine.dispose()

    assert rows == {verified: "approved", waiting: "waiting_email"}


def test_approval_needs_the_name_and_domain_the_superadmin_saw(run):
    async def scenario():
        found = await company()
        await transaction(verification.set_website, found.id, "acme.com", "ann@acme.com")
        renamed = f"Renamed {uuid.uuid4()}"
        await factories.renamed(found.id, renamed)
        stale = await transaction(
            verification.decide, found.id, True, "root", None, [], (found.name, "acme.com")
        )
        other = await transaction(
            verification.decide, found.id, True, "root", None, [], (renamed, "acme.org")
        )
        fresh = await transaction(
            verification.decide, found.id, True, "root", None, [], (renamed, "acme.com")
        )

        return stale, other, fresh

    assert run(scenario()) == (False, False, True)


def test_a_declined_company_goes_for_review_again_only_after_a_rename(run):
    async def scenario():
        found = await company("Beta")
        await transaction(verification.set_website, found.id, "beta.com", "ann@beta.com")
        await transaction(verification.decide, found.id, False, "root", "Not them", [])
        await factories.renamed(found.id, f"Beta {uuid.uuid4().hex[:6]}")

        return await transaction(companies.get, found.id)

    renamed = run(scenario())

    assert renamed.verification_status == "pending"
    assert renamed.verification_name == renamed.name
    assert renamed.decline_reason is None
