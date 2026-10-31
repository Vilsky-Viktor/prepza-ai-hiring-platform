from testee_common.events.deletions import UserDeleted

from ats.services import accounts


async def handle(data: dict) -> None:
    """A user deleted their account: an ATS's records of them as a candidate go; the ATS
    connections they made stay with their companies, without their id, and each company whose
    connection stops working is told once (a redelivery finds none left to forget)."""
    event = UserDeleted.model_validate(data)
    await accounts.remove_user(event.user_id, event.email)
