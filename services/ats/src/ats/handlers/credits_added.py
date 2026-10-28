import logging
from uuid import UUID

from ats.constants.events import COMPANY_OWNER
from ats.services import ats_candidates

logger = logging.getLogger(__name__)


async def handle(data: dict) -> None:
    """A company got credits: the candidates not invited for lack of credits are invited again.
    Other owners' credits are ignored."""
    if data.get("owner_type") != COMPANY_OWNER:
        return

    try:
        company_id = UUID(str(data.get("owner_id")))
    except ValueError:
        # Retrying can't fix it: dropped, so Pub/Sub doesn't send it again and again.
        logger.warning("Dropped credits.added for a malformed owner %r", data.get("owner_id"))

        return

    await ats_candidates.topped_up(company_id)
