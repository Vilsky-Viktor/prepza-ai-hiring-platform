from uuid import UUID

from ats.constants.events import COMPANY_OWNER
from ats.services import ats_candidates


async def handle(data: dict) -> None:
    """A company got credits: the candidates not invited for lack of credits are invited again.
    Other owners' credits are ignored."""
    if data.get("owner_type") != COMPANY_OWNER:
        return

    # A malformed id raises ValueError: no retry can fix it, so the event is dropped
    # (testee_common.events.unhandleable).
    await ats_candidates.topped_up(UUID(str(data.get("owner_id"))))
