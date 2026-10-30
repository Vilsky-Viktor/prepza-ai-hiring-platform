from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from prepza_common.auth.service_auth import only_from
from prepza_common.config.constants import MAX_UPDATES, UPDATES_CALLER

from library.api.dependencies import ServiceCaller
from library.constants.quality import COMPANY_INTERVIEWS_LINK, PATTERN_SIGNALS_CALLER
from library.schemas.quality import (
    QuestionQuality,
    QuestionUpdateOut,
    QuestionUpdatesIn,
    QuestionUpdatesOut,
    ReportNote,
)
from library.schemas.quality_report import QualitySignalOut
from library.services import admin_quality, quality_signals, question_updates
from library.services import quality as quality_service

router = APIRouter(prefix="/internal/questions", tags=["internal"])


@router.get("/signals")
async def list_signals(
    caller: ServiceCaller, days: int = Query(7, ge=1, le=31)
) -> list[QualitySignalOut]:
    """Questions flagged or replaced in the last `days` across every company and template, for
    generation's weekly pattern job only: it turns them into general rules without any company's
    text, and nothing else may read other companies' questions."""
    only_from(caller, PATTERN_SIGNALS_CALLER)

    return await quality_signals.recent(days)


@router.post("/updates")
async def company_question_updates(
    body: QuestionUpdatesIn, caller: ServiceCaller
) -> QuestionUpdatesOut:
    """The assistant, for its get_updates tool: each question of these companies' interviews
    newly flagged or fixed after `since` and up to `until`, named by its topic: the newest
    MAX_UPDATES of each kind, and how many of each in all."""
    only_from(caller, UPDATES_CALLER)
    rows, counts = await question_updates.between(
        body.company_ids, body.since, body.until, MAX_UPDATES
    )

    return QuestionUpdatesOut(
        items=[
            QuestionUpdateOut(
                kind=kind,
                at=at,
                company_id=company_id,
                title=title,
                topic=topic,
                link=COMPANY_INTERVIEWS_LINK.format(company_id=company_id),
            )
            for kind, at, company_id, title, topic in rows
        ],
        counts=counts,
    )


@router.get("/{question_id}/quality")
async def get_quality(question_id: UUID, caller: ServiceCaller) -> QuestionQuality:
    found = await admin_quality.with_reports(question_id)

    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")

    question, stats, reports = found

    return QuestionQuality(
        text=question.text,
        options=question.options,
        answers=stats.answers if stats else 0,
        option_picks=stats.option_picks if stats else {},
        reports=[ReportNote(reason=report.reason) for report in reports],
        flag=stats.flag if stats else None,
    )


@router.post("/{question_id}/keep", status_code=status.HTTP_204_NO_CONTENT)
async def keep(question_id: UUID, caller: ServiceCaller) -> None:
    """The verifier found nothing wrong: serve the question again and stop flagging it."""
    await quality_service.keep(question_id)


@router.post("/{question_id}/wrong", status_code=status.HTTP_204_NO_CONTENT)
async def mark_wrong(question_id: UUID, caller: ServiceCaller) -> None:
    """For companies, once it has checked the question is in the company's test."""
    await quality_service.mark_wrong(question_id)
