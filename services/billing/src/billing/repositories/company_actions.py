from prepza_common.events import audit
from prepza_common.events.audit_actions import AuditAction, TargetKind
from sqlalchemy.ext.asyncio import AsyncSession

from billing.models.outbox import OutboxEvent


def log(session: AsyncSession, company_id, user_id: str, action: AuditAction) -> None:
    """A member's payment action on the company (a top-up, the currency, the automatic top-up),
    for its action log, through the outbox in the change's own transaction."""
    audit.add(session, OutboxEvent, company_id, user_id, action, TargetKind.COMPANY, company_id)
