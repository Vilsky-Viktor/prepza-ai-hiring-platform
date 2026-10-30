"""An interview's bank opt-out reaches library: interview.privacy_changed saved in the same
transaction as the setting (outbox), newest last."""

import uuid

from sqlalchemy import select

from companies.core.db import Session
from companies.models.outbox import OutboxEvent
from companies.repositories import interviews
from companies.schemas.interviews import InterviewSettings
from companies.services import interview_changes
from tests.integration import factories
from tests.integration.transactions import transaction


def test_keeping_questions_private_and_back_is_sent_to_library_in_order(run):
    async def scenario():
        company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        found = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)

        for keep in (True, False):
            interview = await transaction(interviews.get, found.id)
            await interview_changes.update_settings(
                interview, InterviewSettings(keep_private=keep), "owner", None
            )

        await interview_changes.update_settings(
            interview, InterviewSettings(question_seconds=45), "owner", None
        )

        async with Session() as session:
            sent = list(
                await session.scalars(
                    select(OutboxEvent.data)
                    .where(
                        OutboxEvent.event_type == "interview.privacy_changed",
                        OutboxEvent.data["interview_id"].astext == str(found.id),
                    )
                    .order_by(OutboxEvent.created_at)
                )
            )

        await factories.deleted(company.id)

        return found, company.id, sent

    found, company_id, sent = run(scenario())

    assert [event["keep_private"] for event in sent] == [True, False]
    assert {event["company_id"] for event in sent} == {str(company_id)}
    assert {event["generation_id"] for event in sent} == {str(found.generation_id)}
    assert sent[0]["changed_at"] < sent[1]["changed_at"]
