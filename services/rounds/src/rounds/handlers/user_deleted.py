from prepza_common.events.deletions import UserDeleted

from rounds.services import accounts


async def handle(data: dict) -> None:
    """Accounts deleted a user's account: every session of theirs goes, with its answers, a batch
    at a time."""
    await accounts.remove_user(UserDeleted.model_validate(data).user_id)
