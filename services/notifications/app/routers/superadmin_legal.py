import logging
from typing import Literal

from fastapi import APIRouter, status
from prepza_common.auth.superadmin import SuperadminUser

from app.schemas.legal_notices import LegalNoticeOut
from app.services import legal_notices

logger = logging.getLogger(__name__)

# The admin zone's controls: a superadmin decides a legal document's change is significant and
# has it emailed. Everyone else gets "not found".
router = APIRouter(prefix="/superadmin/legal-notices", tags=["superadmin"])


@router.get("")
async def list_notices(superadmin: SuperadminUser) -> list[LegalNoticeOut]:
    """Each document's current version, and whether its notice can be, is being or was sent."""
    return [LegalNoticeOut(**item) for item in await legal_notices.states()]


@router.post("/{document}", status_code=status.HTTP_204_NO_CONTENT)
async def send_notice(
    document: Literal["terms", "privacy", "dpa"], superadmin: SuperadminUser
) -> None:
    """Emails the change to the document's current version from the next sending hour, and puts
    it in the bell."""
    await legal_notices.ask(document, superadmin.uid)
    logger.warning("Superadmin %s asked for the %s change's notice", superadmin.uid, document)
