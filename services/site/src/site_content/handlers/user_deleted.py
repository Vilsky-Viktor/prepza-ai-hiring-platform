from testee_common.events.deletions import UserDeleted

from site_content.services import accounts


async def handle(data: dict) -> None:
    """A user deleted their account: the contact messages sent from its email that site still
    keeps go."""
    await accounts.remove_user(UserDeleted.model_validate(data).email)
