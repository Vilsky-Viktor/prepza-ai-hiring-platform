from uuid import UUID

from ats.repositories import ats, ats_links
from ats.services import ats as integrations


async def handle(data: dict) -> None:
    """What prepza set up in the company's ATSs is cancelled (as far as each answers), then its
    connections go, with their linked jobs and candidates. Deleting twice deletes nothing more."""
    company_id = UUID(data["company_id"])
    subscriptions = await ats_links.subscriptions(company_id)

    for connection in await ats.connections(company_id):
        await integrations.release(connection, subscriptions)

    await ats.delete_company(company_id)
