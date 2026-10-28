import uuid

import pytest
from prepza_common.config.constants import LEGAL_VERSIONS

from companies.core.db import Session
from companies.models.companies import Member
from companies.repositories import companies, email_reminders
from tests.integration import factories
from tests.integration.transactions import transaction


def test_company_names_are_unique_ignoring_case_until_deleted(run):
    async def scenario():
        first = await factories.company("Unique Co", "ann", "ann@example.com")
        taken = await factories.company("unique co", "bob", "bob@example.com")
        await factories.deleted(first.id)
        freed = await factories.company("UNIQUE CO", "bob", "bob@example.com")

        return first, taken, freed

    first, taken, freed = run(scenario())

    assert first is not None
    assert taken is None
    assert freed is not None and freed.name == "UNIQUE CO"


def test_a_new_company_keeps_the_dpa_version_its_owner_accepted(run):
    async def scenario():
        made = await factories.company(f"DPA {uuid.uuid4()}", "ann", "ann@example.com")
        found = await transaction(companies.get, made.id)
        await factories.deleted(made.id)

        return found

    assert run(scenario()).dpa_version == LEGAL_VERSIONS["dpa"]


@pytest.mark.parametrize("editors_only", [True, False])
def test_members_are_listed_a_page_at_a_time_joined_ones_only(run, editors_only):
    """Owners and admins for the DPA's notice (editors_only), everyone who joined for a campaign
    to companies; never an invite not accepted yet."""
    owner, viewer = f"own-{uuid.uuid4()}", f"view-{uuid.uuid4()}"

    async def scenario():
        made = await factories.company(f"Editors {uuid.uuid4()}", owner, "own@example.com")

        async with Session() as session:
            session.add_all(
                [
                    Member(
                        company_id=made.id, user_id=viewer, invited_email="v@x.io", role="viewer"
                    ),
                    # Invited, not joined yet.
                    Member(company_id=made.id, invited_email="a@x.io", role="admin"),
                ]
            )
            await session.commit()

        # Read from just before this test's members.
        found = await transaction(email_reminders.member_ids, "own-", 5000, editors_only)
        # The next page starts after the owner.
        after = await transaction(email_reminders.member_ids, owner, 5000, editors_only)
        await factories.deleted(made.id)

        return found, after

    found, after = run(scenario())

    assert owner in found and owner not in after
    assert (viewer in found) is not editors_only
    assert None not in found


def test_a_users_companies_are_listed_by_name_in_any_case(run):
    owner = f"abc-{uuid.uuid4()}"
    suffix = uuid.uuid4()

    async def scenario():
        made = [
            await factories.company(f"{name} {suffix}", owner, "own@example.com")
            for name in ("beta", "Alpha", "Gamma")
        ]
        found = await transaction(companies.list_for_user, owner, 0, 10)

        for company in made:
            await factories.deleted(company.id)

        return [company.name for company in found]

    assert run(scenario()) == [f"Alpha {suffix}", f"beta {suffix}", f"Gamma {suffix}"]


def test_a_logo_is_saved_served_and_removed_with_a_new_address_each_time(run):
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 20

    async def scenario():
        company = await factories.company(f"Logo {uuid.uuid4()}", "owner", "owner@example.com")
        await transaction(companies.set_logo, company.id, png, "image/png")
        saved = await transaction(companies.get_logo, company.id)
        version = (await transaction(companies.get, company.id)).logo_version
        await transaction(companies.set_logo, company.id, None, None)

        return saved, version, await transaction(companies.get_logo, company.id)

    saved, version, removed = run(scenario())

    assert saved == (png, "image/png")
    assert version == 1
    assert removed is None


def test_a_company_cant_take_another_companys_name_in_any_case(run):
    async def scenario():
        word = uuid.uuid4().hex[:8]
        first = await factories.company(f"First {word}", "owner", "owner@example.com")
        second = await factories.company(f"Second {word}", "owner", "owner@example.com")
        taken = await factories.renamed(second.id, f"FIRST {word}")
        free = await factories.renamed(second.id, f"Third {word}")

        return first, taken, free, (await transaction(companies.get, second.id)).name, word

    _, taken, free, name, word = run(scenario())

    assert (taken, free, name) == (False, True, f"Third {word}")
