from prepza_common.events.deletions import CompanyDeleted

from library.services import sets


async def handle(event_id: str, data: dict) -> None:
    """Companies deleted a company: every set of its interviews goes, with its bank opt-outs;
    its questions' copies in the shared bank stay."""
    await sets.remove_company(CompanyDeleted.model_validate(data).company_id)
