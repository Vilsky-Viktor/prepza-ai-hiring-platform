from uuid import UUID

from fastapi import APIRouter, status
from testee_common.auth.auth import CurrentUser

from companies.api.dependencies import Via
from companies.schemas.ai_apps import AiAppsIn
from companies.services import company_settings

router = APIRouter(prefix="/companies/{company_id}/ai-apps", tags=["companies"])


@router.put("", status_code=status.HTTP_204_NO_CONTENT)
async def set_ai_apps(company_id: UUID, body: AiAppsIn, user: CurrentUser, via: Via) -> None:
    """Owners and admins allow, or stop, members using the company's data from the AI apps they
    connected. Never through an AI app or the assistant: a person decides, in testee itself."""
    await company_settings.set_ai_apps(company_id, user, body.allowed, via)
