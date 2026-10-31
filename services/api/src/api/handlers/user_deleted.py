from testee_common.events.deletions import UserDeleted

from api.services import accounts


async def handle(data: dict) -> None:
    """A user deleted their account: the keys and web hooks they made stay their companies',
    without the user's id, and their results as a candidate waiting to be sent again to
    companies' web hooks go. Handling it twice changes nothing more."""
    event = UserDeleted.model_validate(data)
    await accounts.remove_user(event.user_id, event.email)
