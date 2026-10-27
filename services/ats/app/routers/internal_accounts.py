from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from prepza_common.auth.user import UserEmailIn

from app.service_auth import ServiceCaller
from app.services import outbox as outbox_service
from app.storage import ats, ats_candidates

router = APIRouter(prefix="/internal", tags=["internal"])


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, body: UserEmailIn, caller: ServiceCaller) -> None:
    """Library, deleting an account: an ATS's records of them as a candidate go; the ATS
    connections they made stay with their companies, without their id, and each company is
    told they need reconnecting."""
    await ats_candidates.delete_email(body.email)
    await ats.forget_maker(user_id)
    await outbox_service.flush_quietly()


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, body: UserEmailIn, caller: ServiceCaller) -> dict:
    """Library, for "Download my data": what ATSs sent about them as a candidate, and the ATS
    connections they made."""
    return jsonable_encoder(
        {
            "ats_candidates": [
                {
                    "email": row.email,
                    "name": row.name,
                    "interview_id": row.interview_id,
                    "status": row.status,
                    "results_sent_at": row.reported_at,
                    "at": row.created_at,
                }
                for row in await ats_candidates.of_email(body.email)
            ],
            "ats_connections": [
                {
                    "company_id": row.company_id,
                    "provider": row.provider,
                    "account": row.account,
                    "at": row.created_at,
                }
                for row in await ats.made_by(user_id)
            ],
        }
    )
