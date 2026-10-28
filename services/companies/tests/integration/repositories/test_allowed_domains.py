import uuid

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from companies.core.db import Session
from companies.repositories import companies
from tests.integration import factories
from tests.integration.transactions import transaction


def test_a_new_company_allows_no_site_until_its_domains_are_saved(run):
    async def scenario():
        company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        fresh = await transaction(companies.get, company.id)
        await transaction(
            companies.set_allowed_domains, company.id, ["jobs.acme.com", "*.acme.com"], True
        )

        return fresh, await transaction(companies.get, company.id)

    fresh, saved = run(scenario())

    assert (fresh.allowed_domains, fresh.allow_localhost) == ([], False)
    assert (saved.allowed_domains, saved.allow_localhost) == (["jobs.acme.com", "*.acme.com"], True)


def test_a_verified_company_keeps_its_domain_and_subdomains_after_the_migration(run):
    async def insert(company_id, name, verified):
        async with Session() as session:
            await session.execute(
                text(
                    "INSERT INTO companies (id, name, verified_domain, created_at) "
                    "VALUES (:id, :name, :verified, now())"
                ),
                {"id": company_id, "name": name, "verified": verified},
            )
            await session.commit()

    verified, unverified = uuid.uuid4(), uuid.uuid4()
    config = Config("alembic.ini")
    command.downgrade(config, "0064")

    try:
        run(insert(verified, f"Verified {verified}", "acme.com"))
        run(insert(unverified, f"Unverified {unverified}", None))
    finally:
        command.upgrade(config, "head")

    assert run(transaction(companies.get, verified)).allowed_domains == ["acme.com", "*.acme.com"]
    assert run(transaction(companies.get, unverified)).allowed_domains == []
