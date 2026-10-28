from prepza_common.events.deletions import CompanyDeleted

from rounds.services import session_removal


async def handle(data: dict) -> None:
    """Companies deleted a company: every session of its interviews goes."""
    await session_removal.remove_company(CompanyDeleted.model_validate(data).company_id)
