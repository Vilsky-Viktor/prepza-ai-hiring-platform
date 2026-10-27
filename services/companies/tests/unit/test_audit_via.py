from uuid import uuid4

from prepza_common.events.audit_actions import (
    ACTION_GROUPS,
    MAX_TARGET_LABEL,
    AuditAction,
    TargetKind,
)

from app.service_auth import REQUEST_VIA
from app.storage import audit

COMPANY_ID = uuid4()


def test_an_action_records_what_its_request_came_through_unless_told():
    """An action through the in-app assistant or an AI app shows as such in the action log, not
    as one done in the app, whichever route records it."""
    token = REQUEST_VIA.set("mcp")

    try:
        through_request = audit.fields(COMPANY_ID, "bob", AuditAction.LOGO_CHANGED)
        told = audit.fields(COMPANY_ID, "bob", AuditAction.LOGO_CHANGED, via="assistant")
    finally:
        REQUEST_VIA.reset(token)

    assert through_request["via"] == "mcp"
    assert told["via"] == "assistant"
    assert audit.fields(COMPANY_ID, "bob", AuditAction.LOGO_CHANGED)["via"] is None


def test_every_action_has_a_group_and_a_long_label_is_cut():
    assert set(ACTION_GROUPS) == set(AuditAction)

    row = audit.fields(
        COMPANY_ID,
        "bob",
        AuditAction.INTERVIEW_RENAMED,
        target_kind=TargetKind.INTERVIEW,
        target_label="x" * (MAX_TARGET_LABEL + 10),
    )

    assert (row["group"], row["target_kind"], len(row["target_label"])) == (
        "interviews",
        "interview",
        MAX_TARGET_LABEL,
    )
