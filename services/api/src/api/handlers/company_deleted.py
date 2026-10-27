from uuid import UUID

from api.repositories import keys, webhooks


async def handle(data: dict) -> None:
    """A company was deleted: its keys and web hooks go. Deleting twice deletes nothing more."""
    company_id = UUID(data["company_id"])
    await keys.remove_company(company_id)
    await webhooks.remove_company(company_id)
