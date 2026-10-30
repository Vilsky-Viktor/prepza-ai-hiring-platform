"""A deleted company's id leaves its AI calls a batch at a time; the costs stay."""

import uuid
from datetime import UTC, datetime

from prepza_common.db import db

from billing.core.db import Session
from billing.models.usage import AiUsage
from billing.repositories import usage
from billing.services import accounts
from billing.services import usage as usage_service
from tests.integration.services.test_ai_usage import call, rows_of

NOW = datetime(2026, 10, 10, 12, tzinfo=UTC)


def test_a_deleted_companys_id_is_emptied_batch_after_batch(run, monkeypatch):
    monkeypatch.setattr(db, "DELETE_BATCH", 2)
    acme = str(uuid.uuid4())
    subject = str(uuid.uuid4())

    async def scenario():
        for _ in range(3):
            await usage_service.record_usage(
                uuid.uuid4().hex, NOW, call(company_id=acme, subject_id=subject)
            )

        await usage.forget(Session, "company_id", acme)

        return await rows_of(AiUsage.subject_id, subject)

    rows = run(scenario())

    assert [row.company_id for row in rows] == [None, None, None]
    assert sum(row.cost for row in rows) == 1.5


def test_a_users_ai_calls_are_in_their_export_until_their_account_goes(run):
    ann, other = f"u-{uuid.uuid4()}", f"u-{uuid.uuid4()}"

    async def scenario():
        await usage_service.record_usage(uuid.uuid4().hex, NOW, call(user_id=ann))
        await usage_service.record_usage(uuid.uuid4().hex, NOW, call(user_id=other))
        exported = await accounts.export(ann)
        await accounts.delete_user(ann)

        return exported, await accounts.export(ann)

    exported, after = run(scenario())

    assert [(row["action"], row["at"]) for row in exported["ai_usage"]] == [
        ("assistant_message", NOW)
    ]
    assert after["ai_usage"] == []
