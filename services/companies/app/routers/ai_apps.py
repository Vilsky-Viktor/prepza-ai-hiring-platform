from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.auth import CurrentUser
from prepza_common.events.audit_actions import AuditAction, TargetKind

from app.constants.ai_apps import AI_APPS_CHANGED_BY_APP
from app.schemas.ai_apps import AiAppsIn
from app.service_auth import Via
from app.services.access import require_editor
from app.storage import audit, companies

router = APIRouter(prefix="/companies/{company_id}/ai-apps", tags=["companies"])


@router.put("", status_code=status.HTTP_204_NO_CONTENT)
async def set_ai_apps(company_id: UUID, body: AiAppsIn, user: CurrentUser, via: Via) -> None:
    """Owners and admins allow, or stop, members using the company's data from the AI apps they
    connected. Never through an AI app or the assistant: a person decides, in prepza itself."""
    if via is not None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, AI_APPS_CHANGED_BY_APP)

    company, _ = await require_editor(user, company_id)
    await companies.set_ai_apps(company.id, body.allowed)
    await audit.record(
        company.id,
        user.uid,
        AuditAction.AI_APPS_CHANGED,
        company.id,
        via=via,
        target_kind=TargetKind.COMPANY,
    )
