from uuid import UUID

from api.services import accounts


async def handle(data: dict) -> None:
    """A company was deleted: its keys and web hooks go. Deleting twice deletes nothing more."""
    await accounts.remove_company(UUID(data["company_id"]))
