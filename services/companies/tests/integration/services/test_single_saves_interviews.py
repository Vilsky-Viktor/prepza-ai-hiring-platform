"""An interview's creation and an owner or admin's change to it are one save with its line in
the action log: when the log's line fails, nothing else is kept, so the retry finds the whole
action still to do."""

import uuid
from types import SimpleNamespace

import pytest
from fake_redis import FakeRedis
from sqlalchemy import func, select

from companies.core.db import Session
from companies.integrations import billing, library
from companies.integrations import generation as generation_api
from companies.models.interviews import Interview
from companies.repositories import audit, interviews
from companies.schemas.interviews import InterviewSettings
from companies.services import interview_changes, interview_creation, interview_removal
from tests.integration import factories
from tests.integration.broken import DatabaseWentAway, broken
from tests.integration.transactions import transaction

TOPIC = uuid.uuid4()


@pytest.fixture(autouse=True)
def calls_elsewhere(monkeypatch):
    """Billing, generation, library and Redis are elsewhere: a paying company, a generation
    started, a template copied and a set of one topic with two questions."""

    async def paid(company_id):
        return True

    async def started(*args):
        return {"id": str(uuid.uuid4()), "language": "en"}

    async def copied(template_id, company_id):
        return {"id": uuid.uuid4(), "title": "Copy", "language": "en", "level": "medium"}

    async def a_set(set_id):
        return {"topics": [{"id": str(TOPIC), "title": "SQL", "question_count": 2}]}

    async def nothing(*args, **kwargs):
        return None

    monkeypatch.setattr(billing, "company_paid", paid)
    monkeypatch.setattr(generation_api, "create", started)
    monkeypatch.setattr(library, "copy_template", copied)
    monkeypatch.setattr(library, "get_set", a_set)
    monkeypatch.setattr(library, "rename_set", nothing)
    monkeypatch.setattr(interview_creation, "get_redis", FakeRedis)
    monkeypatch.setattr(audit, "record_interview", broken)


async def an_interview():
    company = await factories.company(f"Saves {uuid.uuid4()}", "ann", "ann@example.com")
    interview = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
    await transaction(interviews.set_link, interview.id, "on")
    await transaction(interviews.set_title, interview.id, "Backend")
    found = await transaction(interviews.get, interview.id)
    found.set_id = uuid.uuid4()

    return company, found


async def interview_count(company_id) -> int:
    async with Session() as session:
        return await session.scalar(
            select(func.count()).select_from(Interview).where(Interview.company_id == company_id)
        )


@pytest.mark.parametrize("how", ["generated", "template"])
def test_a_new_interview_whose_log_line_fails_isnt_saved(run, how):
    async def scenario():
        company = await factories.company(f"New {uuid.uuid4()}", "ann", "ann@example.com")

        with pytest.raises(DatabaseWentAway):
            if how == "generated":
                await interview_creation.create(company, "ann", "en", "SQL", None)
            else:
                await interview_creation.create_from_template(company, "ann", uuid.uuid4())

        return await interview_count(company.id)

    assert run(scenario()) == 0


@pytest.mark.parametrize("change", ["settings", "title", "topic", "link"])
def test_a_change_whose_log_line_fails_isnt_kept(run, change):
    def kept(row) -> tuple:
        return row.pass_mark, row.title, row.topic_limits, row.link_token

    async def scenario():
        _, interview = await an_interview()
        before = kept(interview)

        with pytest.raises(DatabaseWentAway):
            if change == "settings":
                await interview_changes.update_settings(
                    interview, InterviewSettings(pass_mark=before[0] + 1), "ann", None
                )
            elif change == "title":
                await interview_changes.rename(interview, "Renamed", "ann")
            elif change == "topic":
                await interview_changes.set_topic_limit(interview, TOPIC, 1, "ann")
            else:
                await interview_changes.set_link(interview, False, "ann")

        return before, kept(await transaction(interviews.get, interview.id))

    before, after = run(scenario())

    assert after == before


def test_a_deletion_whose_log_line_fails_keeps_the_interview(run):
    async def scenario():
        company, interview = await an_interview()

        with pytest.raises(DatabaseWentAway):
            await interview_removal.remove(SimpleNamespace(**vars(interview)), "ann")

        return await interview_count(company.id)

    assert run(scenario()) == 1
