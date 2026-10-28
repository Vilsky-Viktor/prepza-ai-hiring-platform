"""An interview's totals for each candidate and its topics' numbers of questions, against the
real database: the page's three numbers follow each change, and the last topic with questions
can't be set to 0, even by two changes at once."""

import os
import uuid

import pytest
from fastapi import HTTPException
from prepza_common.auth.user import User
from prepza_common.db.lock_waits import hold_first_commit, race

from companies.api.v1.interview_questions import set_topic_limit
from companies.api.v1.interviews import get_interview
from companies.integrations import library
from companies.repositories import companies, interviews
from companies.schemas.interviews import InterviewSettings, TopicLimitIn
from companies.services import set_cache

SQL = uuid.uuid4()
GIT = uuid.uuid4()


@pytest.fixture
def two_topics(monkeypatch):
    """Library's set: SQL with 20 questions, Git with 5."""
    found = {
        "id": str(uuid.uuid4()),
        "title": "Backend",
        "topics": [
            {"id": str(SQL), "title": "SQL", "subtopics": [], "question_count": 20},
            {"id": str(GIT), "title": "Git", "subtopics": [], "question_count": 5},
        ],
    }

    async def get_set(_set_id):
        return found

    monkeypatch.setattr(library, "get_set", get_set)
    monkeypatch.setattr(set_cache, "get_set", get_set)


async def an_interview() -> tuple:
    """A new company's interview from a template, at 60 seconds a question, and its owner."""
    uid = f"owner-{uuid.uuid4().hex}"
    company = await companies.create(f"Acme {uuid.uuid4()}", uid, f"{uid}@example.com")
    interview = await interviews.create_from_template(company.id, uuid.uuid4(), "Backend", "en", 60)
    owner = User(uid=uid, email=f"{uid}@example.com", email_verified=True)

    return interview, owner


def numbers(detail) -> tuple:
    return detail.total_questions, detail.question_seconds, detail.total_minutes


def test_the_three_numbers_follow_each_topic_and_time_change(run, two_topics):
    async def scenario():
        interview, owner = await an_interview()
        seen = [numbers(await get_interview(interview.id, owner))]
        await set_topic_limit(interview.id, SQL, TopicLimitIn(limit=16), owner)
        seen.append(numbers(await get_interview(interview.id, owner)))
        await set_topic_limit(interview.id, GIT, TopicLimitIn(limit=0), owner)
        seen.append(numbers(await get_interview(interview.id, owner)))
        await interviews.update_settings(interview.id, InterviewSettings(question_seconds=45))
        seen.append(numbers(await get_interview(interview.id, owner)))

        return seen

    assert run(scenario()) == [
        # SQL's default 10 and all 5 of Git's, a minute each.
        (15, 60, 15),
        (21, 60, 21),
        (16, 60, 16),
        # 16 questions at 45 seconds are 12 minutes.
        (16, 45, 12),
    ]


def test_the_last_two_topics_set_to_0_at_once_leave_one_with_questions(run, monkeypatch):
    """The second change waits on the row the first holds, so without the row lock both would
    read the numbers before either saves."""

    def keeps(limits: dict[str, int]) -> bool:
        return any(limits.get(str(topic), 10) > 0 for topic in (SQL, GIT))

    async def scenario():
        interview, _ = await an_interview()

        held = hold_first_commit(monkeypatch, interviews)
        results = await race(
            os.environ["DATABASE_URL"],
            held,
            *(interviews.set_topic_limit(interview.id, topic, 0, keeps) for topic in (SQL, GIT)),
        )

        return results, (await interviews.get(interview.id)).topic_limits

    results, limits = run(scenario())

    assert results == (True, False)
    assert list(limits.values()) == [0]


def test_setting_the_last_topic_with_questions_to_0_is_refused(run, two_topics):
    async def scenario():
        interview, owner = await an_interview()
        await set_topic_limit(interview.id, GIT, TopicLimitIn(limit=0), owner)

        with pytest.raises(HTTPException) as refused:
            await set_topic_limit(interview.id, SQL, TopicLimitIn(limit=0), owner)

        return refused.value, (await interviews.get(interview.id)).topic_limits

    refused, limits = run(scenario())

    assert refused.status_code == 422
    assert refused.detail == "An interview needs at least one topic with questions."
    assert limits == {str(GIT): 0}


def test_an_interview_names_its_company(run, two_topics):
    """So a link to it can be built from the interview alone (the assistant's rows)."""

    async def scenario():
        interview, owner = await an_interview()
        detail = await get_interview(interview.id, owner)
        await companies.delete(interview.company_id)

        return detail.company_id, interview.company_id

    found, expected = run(scenario())

    assert found == expected
