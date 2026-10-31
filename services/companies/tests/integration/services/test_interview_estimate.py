"""An interview's totals for each candidate and its topics' numbers of questions, against the
real database: the page's three numbers follow each change, the last topic with questions can't
be set to 0, and the total never goes over the cap, even by two changes at once."""

import os
import uuid

import pytest
from fastapi import HTTPException
from testee_common.auth.user import User
from testee_common.db.lock_waits import hold_first_commit, race

from companies.api.v1.interview_questions import set_topic_limit
from companies.api.v1.interviews import get_interview
from companies.integrations import library
from companies.repositories import interviews
from companies.schemas.interviews import InterviewSettings, TopicLimitIn
from companies.services import interview_changes, set_cache
from tests.integration import factories
from tests.integration.transactions import transaction

SQL = uuid.uuid4()
GIT = uuid.uuid4()


def use_set(monkeypatch, topics: list[tuple]) -> dict:
    """Library's set with `topics` (id, title, number of questions); the test may change it."""
    found = {
        "id": str(uuid.uuid4()),
        "title": "Backend",
        "topics": [
            {"id": str(key), "title": title, "subtopics": [], "question_count": size}
            for key, title, size in topics
        ],
    }

    async def get_set(_set_id):
        return found

    monkeypatch.setattr(library, "get_set", get_set)
    monkeypatch.setattr(set_cache, "get_set", get_set)

    return found


@pytest.fixture
def two_topics(monkeypatch):
    """Library's set: SQL with 20 questions, Git with 5."""
    return use_set(monkeypatch, [(SQL, "SQL", 20), (GIT, "Git", 5)])


@pytest.fixture
def ten_topics(monkeypatch):
    """Library's set: ten topics of 50 questions, 6 each for a candidate by default (60)."""
    return use_set(monkeypatch, [(uuid.uuid4(), f"Topic {index}", 50) for index in range(10)])


async def an_interview() -> tuple:
    """A new company's interview from a template, at 60 seconds a question, and its owner."""
    uid = f"owner-{uuid.uuid4().hex}"
    company = await factories.company(f"Acme {uuid.uuid4()}", uid, f"{uid}@example.com")
    interview = await transaction(
        interviews.create_from_template, company.id, uuid.uuid4(), "Backend", "en", 60
    )
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
        await transaction(
            interviews.update_settings, interview.id, InterviewSettings(question_seconds=45)
        )
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


def test_the_last_two_topics_set_to_0_at_once_leave_one_with_questions(
    run, monkeypatch, two_topics
):
    """The second change waits on the row the first holds, so without the row lock both would
    read the numbers before either saves."""

    async def scenario():
        interview, _ = await an_interview()

        return await race_limits(monkeypatch, interview, (SQL, 0), (GIT, 0))

    results, limits = run(scenario())

    assert results[0] is None
    assert results[1].detail == "An interview needs at least one topic with questions."
    assert limits == {str(SQL): 0, str(GIT): 5}


async def race_limits(monkeypatch, interview, first: tuple, second: tuple) -> tuple:
    """Two topics' numbers changed at once, the first change's commit held until the second
    waits on its lock; both results and the numbers stored after."""
    held = hold_first_commit(monkeypatch, interview_changes)
    results = await race(
        os.environ["DATABASE_URL"],
        held,
        *(
            interview_changes.set_topic_limit(interview, uuid.UUID(str(topic)), limit, "ann")
            for topic, limit in (first, second)
        ),
    )

    return results, (await transaction(interviews.get, interview.id)).topic_limits


def test_setting_the_last_topic_with_questions_to_0_is_refused(run, two_topics):
    async def scenario():
        interview, owner = await an_interview()
        await set_topic_limit(interview.id, GIT, TopicLimitIn(limit=0), owner)

        with pytest.raises(HTTPException) as refused:
            await set_topic_limit(interview.id, SQL, TopicLimitIn(limit=0), owner)

        return refused.value, (await transaction(interviews.get, interview.id)).topic_limits

    refused, limits = run(scenario())

    assert refused.status_code == 422
    assert refused.detail == "An interview needs at least one topic with questions."
    assert limits == {str(SQL): 10, str(GIT): 0}


def test_an_interview_names_its_company(run, two_topics):
    """So a link to it can be built from the interview alone (the assistant's rows)."""

    async def scenario():
        interview, owner = await an_interview()
        detail = await get_interview(interview.id, owner)
        await factories.deleted(interview.company_id)

        return detail.company_id, interview.company_id

    found, expected = run(scenario())

    assert found == expected


def test_a_change_over_the_cap_is_refused_and_changes_nothing(run, ten_topics):
    topic = ten_topics["topics"][0]["id"]

    async def scenario():
        interview, owner = await an_interview()
        detail = await get_interview(interview.id, owner)

        with pytest.raises(HTTPException) as refused:
            await set_topic_limit(interview.id, uuid.UUID(topic), TopicLimitIn(limit=7), owner)

        stored = (await transaction(interviews.get, interview.id)).topic_limits

        return detail, refused.value, stored

    detail, refused, stored = run(scenario())

    assert [item.question_limit for item in detail.topics] == [6] * 10
    assert (detail.total_questions, detail.max_questions) == (60, 60)
    assert (refused.status_code, refused.code) == (422, "too_many_questions")
    assert refused.detail == "At most 60 questions per candidate; 0 left."
    assert stored == {}


def test_two_raises_at_once_never_take_the_total_over_the_cap(run, monkeypatch, ten_topics):
    """6 questions are free: each raise takes them all, so only the first is kept."""
    first, second, third = (topic["id"] for topic in ten_topics["topics"][:3])

    async def scenario():
        interview, owner = await an_interview()
        await set_topic_limit(interview.id, uuid.UUID(first), TopicLimitIn(limit=0), owner)

        return await race_limits(monkeypatch, interview, (second, 12), (third, 12))

    results, limits = run(scenario())

    assert results[0] is None
    assert results[1].detail == "At most 60 questions per candidate; 0 left."
    assert (limits[second], limits[third], sum(limits.values())) == (12, 6, 60)


def test_a_topic_added_later_gets_the_room_left(run, monkeypatch):
    found = use_set(monkeypatch, [(uuid.uuid4(), f"Topic {index}", 50) for index in range(6)])
    first = uuid.UUID(found["topics"][0]["id"])

    async def scenario():
        interview, owner = await an_interview()
        await set_topic_limit(interview.id, first, TopicLimitIn(limit=9), owner)
        found["topics"] += [
            {"id": str(uuid.uuid4()), "title": title, "subtopics": [], "question_count": 50}
            for title in ("Added", "Added after")
        ]

        return await get_interview(interview.id, owner)

    detail = run(scenario())

    # 59 stored: the first added topic gets the 1 left, the next none.
    assert [item.question_limit for item in detail.topics] == [9, 10, 10, 10, 10, 10, 1, 0]
    assert detail.total_questions == 60
