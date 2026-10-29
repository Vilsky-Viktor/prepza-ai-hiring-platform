from uuid import uuid4

from companies.api.v1.companies import company_out
from companies.services import company_views
from tests.integration import factories


def test_the_list_counts_each_companys_interviews_and_team_with_pending_invites(run):
    async def scenario():
        made = await factories.team("list")
        await factories.member(made.company.id, f"pending-{uuid4().hex}@example.com", "viewer", {})
        rows = await company_views.listed(made.owner, 0, 10)
        listed = [company_out(item, made.owner, "en", count) for item, count in rows]
        await factories.deleted(made.company.id)

        return listed

    [found] = run(scenario())

    # The owner, an admin and a viewer who joined, and one invited.
    assert (found.interview_count, found.member_count) == (1, 4)
