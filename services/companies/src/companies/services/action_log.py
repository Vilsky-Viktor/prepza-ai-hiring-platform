from datetime import datetime

from companies.core.db import Session
from companies.helpers.audit import audit_event_out
from companies.repositories import action_names, audit
from companies.schemas.audit import ActionOut


async def page(
    company_id,
    offset: int,
    limit: int,
    user_id: str | None = None,
    group: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[ActionOut]:
    """A page of the log, newest first, each action with who took it and what it was about,
    found in one query each; only one member's, one group's, or those from `start` and before
    `end`."""
    async with Session() as session:
        events = await audit.list_for_company(
            session, company_id, offset, limit, user_id, group, start, end
        )
        emails = await action_names.member_emails(
            session, company_id, [event.user_id for event in events]
        )
        targets = await action_names.target_names(
            session, company_id, [event.target_id for event in events if event.target_id]
        )

    return [
        ActionOut(
            **audit_event_out(event).model_dump(),
            id=event.id,
            group=event.group,
            user_email=emails.get(event.user_id),
            target_kind=event.target_kind,
            target=targets.get(event.target_id) or event.target_label,
            removed=event.removed,
        )
        for event in events
    ]
