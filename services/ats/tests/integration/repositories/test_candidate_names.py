import uuid

from ats.constants.ats import AtsProvider
from ats.repositories import ats, ats_candidates, ats_links

STAGE = {"id": "assessment", "name": "Assessment"}


def test_an_ats_candidates_name_is_kept_once_and_a_redelivery_keeps_the_first(run):
    async def scenario():
        company, interview = uuid.uuid4(), uuid.uuid4()
        await ats.connect(company, AtsProvider.WORKABLE, "acme", "sealed", "ann")
        connection = await ats.connection(company, AtsProvider.WORKABLE)
        link = await ats_links.add_link(
            company, connection.id, interview, {"id": "A1", "name": "Clerk"}, STAGE, "ann"
        )
        first = await ats_candidates.add(connection.id, link, interview, "c-1", "a@x.com", "Ann")
        again = await ats_candidates.add(connection.id, link, interview, "c-1", "a@x.com", "Bo")

        return first, again

    first, again = run(scenario())

    assert (first.id, first.name) == (again.id, "Ann")
