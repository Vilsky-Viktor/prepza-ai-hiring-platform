from datetime import UTC, datetime

from fastapi import APIRouter, status
from prepza_common.auth.google import Invoker

from billing.constants.usage import CHANGES_KEEP_DAYS, USAGE_KEEP_DAYS
from billing.repositories import usage
from billing.services import limit_values
from billing.services import outbox as outbox_service
from billing.services.auto_top_up_prices import check_prices
from billing.services.reconciliation import reconcile

router = APIRouter(
    prefix="/internal/schedules",
    tags=["schedules"],
    dependencies=[Invoker],
    include_in_schema=False,
)


@router.post("/limits", status_code=status.HTTP_204_NO_CONTENT)
async def sync_limits() -> None:
    """Every 5 minutes: the edited limits written to Redis again, so a wipe heals itself."""
    await limit_values.sync()


@router.post("/retention", status_code=status.HTTP_204_NO_CONTENT)
async def retention() -> None:
    """Daily: AI usage and limit hits past 13 months, limit changes past 24."""
    await usage.drop_old(datetime.now(UTC), USAGE_KEEP_DAYS, CHANGES_KEEP_DAYS)


@router.post("/outbox", status_code=status.HTTP_204_NO_CONTENT)
async def flush_outbox() -> None:
    """Every minute, from Cloud Scheduler: publishes events that weren't published right after
    their change."""
    await outbox_service.flush()


@router.post("/reconcile", status_code=status.HTTP_204_NO_CONTENT)
async def reconcile_with_paddle() -> None:
    """Daily: what Paddle's web hooks of the last week should have done, done again from Paddle's
    records (services/reconciliation.py)."""
    await reconcile(datetime.now(UTC))


@router.post("/auto-top-up-prices", status_code=status.HTTP_204_NO_CONTENT)
async def check_auto_top_up_prices() -> None:
    """Daily: a new price for an automatic top-up is announced to its company at least 30 days
    before charges cost it (services/auto_top_up_prices.py)."""
    await check_prices(datetime.now(UTC))
