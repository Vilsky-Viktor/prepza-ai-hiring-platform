"""An owner or admin's choices about paying: the automatic top-up and the currency. Billing saves
them; the action log records each after it answers."""

from uuid import UUID

from prepza_common.events.audit_actions import AuditAction, TargetKind

from companies.integrations import billing_prices as billing
from companies.services import audit_records


async def turn_on_auto_top_up(
    company_id: UUID, settings: dict, user_id: str, country: str | None, language: str
) -> dict:
    """Sets it up, or changes a running one; what each charge buys is named on its invoice in
    `language`."""
    was_on = (await billing.auto_top_up(company_id))["on"]
    saved = await billing.turn_on_auto_top_up(
        company_id, settings, user_id, country, language=language
    )
    action = AuditAction.AUTO_TOP_UP_CHANGED if was_on else AuditAction.AUTO_TOP_UP_SET
    await audit_records.record(
        company_id, user_id, action, company_id, target_kind=TargetKind.COMPANY
    )

    return saved


async def turn_off_auto_top_up(company_id: UUID, user_id: str) -> None:
    await billing.turn_off_auto_top_up(company_id)
    await audit_records.record(
        company_id,
        user_id,
        AuditAction.AUTO_TOP_UP_STOPPED,
        company_id,
        target_kind=TargetKind.COMPANY,
    )


async def choose_currency(company_id: UUID, currency: str, user_id: str) -> dict:
    chosen = await billing.choose_currency(company_id, currency)
    await audit_records.record(
        company_id,
        user_id,
        AuditAction.CURRENCY_CHANGED,
        company_id,
        target_kind=TargetKind.COMPANY,
    )

    return chosen
