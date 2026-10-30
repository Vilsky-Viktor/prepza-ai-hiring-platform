import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Query, status

from library.api.dependencies import ServiceCaller
from library.constants.bank import MAX_BANK_CANDIDATES
from library.schemas.bank import BankCandidate, BankCheckIn
from library.services import bank

router = APIRouter(prefix="/internal/bank", tags=["internal"])


@router.get("/candidates")
async def list_candidates(
    caller: ServiceCaller,
    limit: int = Query(MAX_BANK_CANDIDATES, ge=1, le=MAX_BANK_CANDIDATES),
    after: uuid.UUID | None = None,
) -> list[BankCandidate]:
    """Companies' questions for generation's bank filter, in id order after `after`."""
    return await bank.candidates(limit, after)


@router.put("/checks", status_code=status.HTTP_204_NO_CONTENT)
async def save_checks(
    body: Annotated[list[BankCheckIn], Body(max_length=MAX_BANK_CANDIDATES)],
    caller: ServiceCaller,
) -> None:
    """The filter's verdicts; the proven questions that passed join the bank."""
    await bank.save_checks(body)
