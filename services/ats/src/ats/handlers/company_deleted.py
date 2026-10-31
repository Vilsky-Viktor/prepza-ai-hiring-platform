from uuid import UUID

from ats.services import accounts


async def handle(data: dict) -> None:
    """What testee set up in the company's ATSs is cancelled (as far as each answers), then its
    connections go, with their linked jobs and candidates. Deleting twice deletes nothing more."""
    await accounts.remove_company(UUID(data["company_id"]))
