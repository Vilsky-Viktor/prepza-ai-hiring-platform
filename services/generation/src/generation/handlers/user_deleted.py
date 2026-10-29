from prepza_common.events.deletions import UserDeleted

from generation.services import accounts


async def handle(data: dict) -> None:
    """A user deleted their account: their generations stay with their company, without their
    id."""
    await accounts.delete_user(UserDeleted.model_validate(data).user_id)
