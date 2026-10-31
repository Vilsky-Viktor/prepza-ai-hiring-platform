from testee_common.events.deletions import UserDeleted

from assistant.services import accounts


async def handle(data: dict) -> None:
    """A user deleted their account: their conversations go, with every message and tool call,
    the actions they hadn't confirmed yet, and their connected AI apps (whose access stops).
    Deleting twice deletes nothing more."""
    await accounts.delete_user(UserDeleted.model_validate(data).user_id)
