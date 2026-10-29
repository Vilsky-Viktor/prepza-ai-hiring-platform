from prepza_common.events.deletions import UserDeleted

from library.services.user_data import delete_data


async def handle(event_id: str, data: dict) -> None:
    """Accounts deleted a user's account: the votes and reports they gave on questions go."""
    await delete_data(UserDeleted.model_validate(data).user_id)
