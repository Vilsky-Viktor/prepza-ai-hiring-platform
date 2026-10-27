# A member's action in a service other than companies, for the company's action log: saved in
# the service's outbox in the change's transaction, so it's sent exactly when the change happens
# and retried until companies stores it (once, by the event's id).
from prepza_common.events import outbox
from prepza_common.events.audit_actions import (
    AUDIT_RECORDED,
    MAX_TARGET_LABEL,
    AuditAction,
    TargetKind,
)


def add(
    session,
    outbox_model,
    company_id,
    user_id: str,
    action: AuditAction,
    target_kind: TargetKind | None = None,
    target_id=None,
    target_label: str | None = None,
    removed: list[str] | None = None,
) -> None:
    """The outbox row's time goes with it as when it happened (pubsub.occurred_at), so a late or
    out-of-order delivery keeps its place in the log. `removed`: what the action took away (an
    API key's permissions)."""
    outbox.add(
        session,
        outbox_model,
        AUDIT_RECORDED,
        {
            "company_id": str(company_id),
            "user_id": user_id,
            "action": action,
            "target_kind": target_kind,
            "target_id": str(target_id) if target_id else None,
            "target_label": target_label[:MAX_TARGET_LABEL] if target_label else None,
            "removed": removed,
        },
    )
