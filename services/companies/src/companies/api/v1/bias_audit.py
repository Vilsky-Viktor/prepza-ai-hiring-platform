from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response
from testee_common.auth.auth import CurrentUser

from companies.constants.bias_audit import FILE_NAME, NOT_OWNER
from companies.services import bias_audit
from companies.services.access import require_owner

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/{company_id}/bias-audit", response_class=Response)
async def export_bias_audit(
    company_id: UUID,
    user: CurrentUser,
    interview_id: UUID | None = None,
    start: Annotated[datetime | None, Query(alias="from")] = None,
    end: Annotated[datetime | None, Query(alias="to")] = None,
) -> Response:
    """A CSV for an independent bias audit (NYC Local Law 144, the EEOC's four-fifths rule): a
    row for each candidate who finished with a grade, with their id, the email the company joins
    its own self-reported categories on, the interview, the day they finished, their grade, the
    pass mark, whether they passed and whether they scored above the interview's median. Only
    one interview's (`interview_id`), or those finished from `from` and before `to`. testee holds
    no protected characteristics; for the owner only, counted per company a day, and recorded in
    the action log."""
    company = await require_owner(user, company_id, NOT_OWNER)
    text = await bias_audit.export(company, user.uid, interview_id, start, end)
    name = FILE_NAME.format(day=datetime.now(UTC).date().isoformat())

    return Response(
        text,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{name}"',
            "Cache-Control": "no-store",
        },
    )
