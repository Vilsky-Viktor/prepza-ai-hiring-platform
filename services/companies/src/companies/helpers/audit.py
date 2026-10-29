from companies.models.audit import AuditEvent
from companies.schemas.audit import AuditEventOut


def audit_event_out(row: AuditEvent) -> AuditEventOut:
    return AuditEventOut(
        user_id=row.user_id,
        action=row.action,
        target_id=row.target_id,
        via=row.via,
        key_id=row.key_id,
        created_at=row.created_at,
    )
