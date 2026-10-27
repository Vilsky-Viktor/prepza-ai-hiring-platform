import uuid

import pytest
from prepza_common.config.constants import LEGAL_VERSIONS

from app.models.companies import Member
from app.storage import companies, email_reminders
from app.storage.db import Session


def test_company_names_are_unique_ignoring_case_until_deleted(run):
    async def scenario():
        first = await companies.create("Unique Co", "ann", "ann@example.com")
        taken = await companies.create("unique co", "bob", "bob@example.com")
        await companies.delete(first.id)
        freed = await companies.create("UNIQUE CO", "bob", "bob@example.com")

        return first, taken, freed

    first, taken, freed = run(scenario())

    assert first is not None
    assert taken is None
    assert freed is not None and freed.name == "UNIQUE CO"


def test_a_new_company_keeps_the_dpa_version_its_owner_accepted(run):
    async def scenario():
        made = await companies.create(f"DPA {uuid.uuid4()}", "ann", "ann@example.com")
        found = await companies.get(made.id)
        await companies.delete(made.id)

        return found

    assert run(scenario()).dpa_version == LEGAL_VERSIONS["dpa"]


@pytest.mark.parametrize("editors_only", [True, False])
def test_members_are_listed_a_page_at_a_time_joined_ones_only(run, editors_only):
    """Owners and admins for the DPA's notice (editors_only), everyone who joined for a campaign
    to companies; never an invite not accepted yet."""
    owner, viewer = f"own-{uuid.uuid4()}", f"view-{uuid.uuid4()}"

    async def scenario():
        made = await companies.create(f"Editors {uuid.uuid4()}", owner, "own@example.com")

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
        found = await email_reminders.member_ids("own-", 5000, editors_only)
        # The next page starts after the owner.
        after = await email_reminders.member_ids(owner, 5000, editors_only)
        await companies.delete(made.id)

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
            await companies.create(f"{name} {suffix}", owner, "own@example.com")
            for name in ("beta", "Alpha", "Gamma")
        ]
        found = await companies.list_for_user(owner, 0, 10)

        for company in made:
            await companies.delete(company.id)

        return [company.name for company in found]

    assert run(scenario()) == [f"Alpha {suffix}", f"beta {suffix}", f"Gamma {suffix}"]
