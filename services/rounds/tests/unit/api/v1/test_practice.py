import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from prepza_common.auth.auth import current_user
from prepza_common.auth.user import User
from prepza_common.config.constants import RATE_LIMITED
from prepza_common.limits.limit_list import LIMITS

from rounds.integrations import library
from rounds.main import app
from rounds.repositories import practice_sessions, sessions

TEMPLATE_ID = uuid.uuid4()
ROUND_ID = uuid.uuid4()


def options():
    return [{"answer": "right", "correct": True}, {"answer": "wrong", "correct": False}]


def content(questions_per_topic):
    return {
        "id": str(TEMPLATE_ID),
        "title": "Backend",
        "level": "medium",
        "topics": [
            {
                "id": str(uuid.uuid4()),
                "title": "Python",
                "questions": [
                    {"id": str(uuid.uuid4()), "text": f"Q{index}?", "options": options()}
                    for index in range(questions_per_topic)
                ],
            }
        ],
    }


def section(status, answers=(), user_id="ann"):
    question_id = str(uuid.uuid4())

    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user_id,
        practice=True,
        candidate_invite_id=ROUND_ID,
        interview_set_id=TEMPLATE_ID,
        topic_title="Python",
        status=status,
        final_score=50 if status == "finished" else None,
        started_at=datetime.now(UTC),
        questions=[
            {"id": question_id, "text": "Q?", "options": options()},
            {"id": str(uuid.uuid4()), "text": "Unanswered?", "options": options()},
        ],
        answers=[
            SimpleNamespace(
                id=uuid.uuid4(),
                question_id=uuid.UUID(question_id),
                option_index=0,
                picks=None,
                timed_out=False,
                correct=True,
                score=100,
                seconds=20,
            )
            for _ in answers
        ],
    )


@pytest.fixture(autouse=True)
def signed_in():
    app.dependency_overrides[current_user] = lambda: User(
        uid="ann", email="ann@example.com", email_verified=True
    )
    yield
    app.dependency_overrides.clear()


def test_a_round_takes_up_to_ten_fresh_questions_a_topic_and_only_the_first_counts(
    client, monkeypatch
):
    created = {}

    async def fake_content(template_id):
        return content(14)

    async def fake_create(user_id, round_id, topics, seconds, preview=False, practice=False):
        created.update(
            user_id=user_id, topics=topics, seconds=seconds, preview=preview, practice=practice
        )

        return [SimpleNamespace(id=uuid.uuid4())]

    earlier = []

    async def fake_practiced(user_id, template_id):
        return bool(earlier)

    monkeypatch.setattr(library, "practice_content", fake_content)
    monkeypatch.setattr(sessions, "create_many", fake_create)
    monkeypatch.setattr(practice_sessions, "practiced", fake_practiced)

    response = client.post(f"/practice/{TEMPLATE_ID}")

    assert response.status_code == 201
    assert len(created["topics"][0].questions) == 10
    assert (created["user_id"], created["seconds"], created["practice"]) == ("ann", 60, True)
    # The first round counts in the questions' statistics; a later one doesn't.
    assert created["preview"] is False

    earlier.append(section("finished"))
    client.post(f"/practice/{TEMPLATE_ID}")

    assert created["preview"] is True


@pytest.mark.parametrize(("level", "edited", "seconds"), [("hard", None, 75), ("basic", 45, 45)])
def test_a_rounds_questions_have_the_seconds_of_the_templates_level(
    client, monkeypatch, redis, level, edited, seconds
):
    """As a company's new test of that level has them: as set in Controls, or the default."""
    created = {}

    if edited:
        redis.limits[f"QUESTION_SECONDS_{level.upper()}"] = edited

    async def fake_content(template_id):
        return {**content(10), "level": level}

    async def fake_create(user_id, round_id, topics, seconds, preview=False, practice=False):
        created["seconds"] = seconds

        return [SimpleNamespace(id=uuid.uuid4())]

    async def fake_practiced(user_id, template_id):
        return False

    monkeypatch.setattr(library, "practice_content", fake_content)
    monkeypatch.setattr(sessions, "create_many", fake_create)
    monkeypatch.setattr(practice_sessions, "practiced", fake_practiced)

    assert client.post(f"/practice/{TEMPLATE_ID}").status_code == 201
    assert created["seconds"] == seconds


def test_a_test_without_practice_questions_says_so(client, monkeypatch):
    async def empty(template_id):
        return {**content(0), "topics": []}

    monkeypatch.setattr(library, "practice_content", empty)

    response = client.post(f"/practice/{TEMPLATE_ID}")

    assert response.status_code == 409
    assert response.json()["detail"] == "This interview has no practice questions yet."


def test_a_finished_round_shows_every_right_answer_an_open_one_none(client, monkeypatch):
    rows = [section("finished", answers=[1])]

    async def fake_list(round_id):
        return rows

    async def fake_set(set_id):
        return {"title": "Backend"}

    monkeypatch.setattr(sessions, "list_for_invite", fake_list)
    monkeypatch.setattr(library, "get_set", fake_set)

    finished = client.get(f"/practice/rounds/{ROUND_ID}").json()
    rows[0] = section("in_progress")
    still_open = client.get(f"/practice/rounds/{ROUND_ID}").json()

    # One right of two: 50%. The unanswered question shows its right answer too.
    assert (finished["finished"], finished["grade"]) == (True, 50)
    assert (finished["answered"], finished["total"]) == (1, 2)
    assert [item["correct_option_index"] for item in finished["topics"][0]["review"]] == [0, 0]
    assert (still_open["finished"], still_open["topics"][0]["review"]) == (False, [])
    assert still_open["open_session_id"] == str(rows[0].id)


def test_someone_else_cant_see_a_round(client, monkeypatch):
    async def fake_list(round_id):
        return [section("finished", user_id="bob")]

    monkeypatch.setattr(sessions, "list_for_invite", fake_list)

    assert client.get(f"/practice/rounds/{ROUND_ID}").status_code == 404


def test_the_history_lists_a_page_of_rounds_newest_first_with_their_grades(client, monkeypatch):
    first = section("finished", answers=[1])
    second = section("in_progress")
    second.candidate_invite_id = uuid.uuid4()

    pages = []

    async def fake_rounds(user_id, template_id, offset, limit):
        pages.append((offset, limit))

        return [first, second]

    monkeypatch.setattr(practice_sessions, "practice_rounds", fake_rounds)

    rounds = client.get(f"/practice/{TEMPLATE_ID}/rounds?offset=20&limit=20").json()

    assert pages == [(20, 20)]

    # The open round has none of its two answered; the finished one, one of two.
    assert [(row["finished"], row["progress"], row["grade"]) for row in rounds] == [
        (False, 0, None),
        (True, 50, 50),
    ]


def test_each_topic_shows_how_far_the_latest_round_got(client, monkeypatch):
    older = section("finished", answers=[1])
    older.started_at = datetime(2026, 10, 5, 9, tzinfo=UTC)
    latest = section("in_progress", answers=[1])
    latest.candidate_invite_id = uuid.uuid4()
    latest.topic_id = uuid.uuid4()
    older.topic_id = latest.topic_id
    latest.started_at = datetime(2026, 10, 5, 10, tzinfo=UTC)

    async def fake_rounds(user_id, template_id, offset, limit):
        # Only the latest round is asked for; the older one shows it's picked again here.
        assert (offset, limit) == (0, 1)

        return [older, latest]

    monkeypatch.setattr(practice_sessions, "practice_rounds", fake_rounds)

    progress = client.get(f"/practice/{TEMPLATE_ID}/progress").json()

    # The latest round, unfinished: one of its two questions answered.
    assert progress == [{"topic_id": str(latest.topic_id), "answered": 1, "total": 2}]


@pytest.mark.parametrize("edited", [None, 3])
def test_a_talent_starts_a_limited_number_of_rounds_an_hour(
    client, monkeypatch, redis, published, edited
):
    """At the limit's edited value, or its default when it isn't edited."""
    allowed = edited or LIMITS["PRACTICE_ROUNDS_PER_HOUR"].default

    if edited:
        redis.limits["PRACTICE_ROUNDS_PER_HOUR"] = edited

    async def fake_content(template_id):
        return content(10)

    async def fake_create(user_id, round_id, topics, seconds, preview=False, practice=False):
        return [SimpleNamespace(id=uuid.uuid4())]

    async def fake_practiced(user_id, template_id):
        return False

    monkeypatch.setattr(library, "practice_content", fake_content)
    monkeypatch.setattr(sessions, "create_many", fake_create)
    monkeypatch.setattr(practice_sessions, "practiced", fake_practiced)

    started = [client.post(f"/practice/{TEMPLATE_ID}").status_code for _ in range(allowed)]
    refused = client.post(f"/practice/{TEMPLATE_ID}")

    assert started == [201] * allowed
    assert refused.status_code == 429
    assert refused.json()["detail"] == RATE_LIMITED
    assert [(data["limit"], data["user_id"]) for _, data in published] == [
        ("PRACTICE_ROUNDS_PER_HOUR", "ann")
    ]
