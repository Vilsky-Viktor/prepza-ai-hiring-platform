import uuid
from datetime import UTC, datetime

import pytest
from fake_redis import FakeRedis
from testee_common.auth.auth import current_user
from testee_common.auth.user import User

from companies.constants.interviews import PREVIEWS_USED_UP, VOICE_PREVIEWS_USED_UP
from companies.constants.invites import NO_PLEDGE
from companies.integrations import library, rounds
from companies.main import app
from companies.models.companies import Company, Member
from companies.models.interviews import Interview
from companies.repositories import companies, interviews
from companies.services import previews as interview_routes

COMPANY_ID = uuid.uuid4()
SET_ID = uuid.uuid4()
SESSION_ID = uuid.uuid4()
USER_KEY = "rate:previews:bob"
COMPANY_KEY = f"rate:previews:company:{COMPANY_ID}"
VOICE_KEY = f"rate:previews:voice:{COMPANY_ID}"


@pytest.fixture
def redis(monkeypatch):
    """The limits' counters, in memory."""
    fake = FakeRedis()
    monkeypatch.setattr(interview_routes, "get_redis", lambda: fake)

    return fake


@pytest.fixture
def started(monkeypatch, redis):
    """Bob, a viewer of the company, and one ready test (taken by voice once `voice` is set);
    returns what rounds was asked for."""
    asked = Asked()
    voice = {"on": False}
    company = Company(id=COMPANY_ID, name="Acme", created_at=datetime.now(UTC))
    company.members = [
        Member(
            company_id=COMPANY_ID,
            user_id="bob",
            invited_email="bob@example.com",
            role="viewer",
            created_at=datetime.now(UTC),
        )
    ]

    def interview(set_id=SET_ID):
        return Interview(
            id=uuid.uuid4(),
            company_id=COMPANY_ID,
            generation_id=None,
            set_id=set_id,
            question_seconds=45,
            topic_limits={},
            voice=voice["on"],
        )

    async def get_interview(session, _interview_id):
        return interview()

    async def get_company(session, _company_id):
        return company

    async def content(_set_id):
        questions = [{"id": str(uuid.uuid4()), "text": "Q?", "options": []} for _ in range(3)]

        return {"id": str(SET_ID), "topics": [{"id": "t1", "title": "SQL", "questions": questions}]}

    async def create_sessions(payload):
        asked.append(payload)

        return [{"id": str(SESSION_ID), "topic_title": "SQL", "status": "in_progress"}]

    monkeypatch.setattr(interviews, "get", get_interview)
    monkeypatch.setattr(companies, "get", get_company)
    monkeypatch.setattr(library, "get_content", content)
    monkeypatch.setattr(rounds, "create_sessions", create_sessions)
    app.dependency_overrides[current_user] = lambda: User(
        uid="bob", email="bob@example.com", email_verified=True
    )

    asked.voice = voice
    yield asked

    app.dependency_overrides.clear()


class Asked(list):
    """What rounds was asked for, and the switch that makes the test a voice one."""


def test_any_member_previews_a_test_as_a_candidate_would_for_free(client, started, redis):
    response = client.post(f"/interviews/{uuid.uuid4()}/preview", json={"pledged": True})

    assert response.status_code == 201
    assert response.json() == {"session_id": str(SESSION_ID)}
    [payload] = started
    # Counted once for the person's hour and once for the company's day.
    assert redis.counts == {USER_KEY: 1, COMPANY_KEY: 1}
    # Marked as a preview, timed like the real test, and with no invite behind it to charge.
    assert payload["preview"] is True
    assert payload["question_seconds"] == 45
    assert payload["user_id"] == "bob"
    assert len(payload["topics"][0]["questions"]) == 3


def test_a_preview_starts_with_the_pledge_as_a_candidates_start_does(client, started, redis):
    response = client.post(f"/interviews/{uuid.uuid4()}/preview")

    assert response.status_code == 422
    assert response.json()["detail"] == NO_PLEDGE
    # Neither counted toward the limits nor started.
    assert started == []
    assert redis.counts == {}


def test_someone_outside_the_company_cant(client, started):
    app.dependency_overrides[current_user] = lambda: User(
        uid="eve", email="eve@example.com", email_verified=True
    )

    assert (
        client.post(f"/interviews/{uuid.uuid4()}/preview", json={"pledged": True}).status_code
        == 404
    )
    assert started == []


def test_previews_over_the_hourly_limit_are_refused(client, started, redis):
    redis.limits["PREVIEWS_PER_USER_HOUR"] = 1

    assert [preview(client).status_code for _ in range(2)] == [201, 429]
    assert len(started) == 1


def test_a_companys_previews_a_day_are_limited_and_the_refusal_says_when_to_try_again(
    client, started, redis
):
    redis.limits["PREVIEWS_PER_COMPANY_DAY"] = 2

    responses = [preview(client) for _ in range(3)]

    assert [response.status_code for response in responses] == [201, 201, 429]
    assert responses[2].json() == {
        "detail": PREVIEWS_USED_UP.format(limit=2, hours=24),
        "code": "rate_limited",
    }
    assert responses[2].headers["Retry-After"] == str(24 * 60 * 60)
    assert len(started) == 2


def test_voice_previews_have_their_own_smaller_daily_limit(client, started, redis):
    """A voice preview spends on reading aloud and hearing answers: 5 a day by default, counted
    apart from the company's other previews, which still start once it's used up."""
    started.voice["on"] = True
    voice = [preview(client) for _ in range(6)]
    started.voice["on"] = False
    clicks = preview(client)

    assert [response.status_code for response in voice] == [201] * 5 + [429]
    assert voice[5].json()["detail"] == VOICE_PREVIEWS_USED_UP.format(limit=5, hours=24)
    assert clicks.status_code == 201
    assert redis.counts == {USER_KEY: 7, VOICE_KEY: 6, COMPANY_KEY: 1}
    assert [payload["voice"] for payload in started] == [True] * 5 + [False]


def test_a_refusal_is_recorded_for_the_company(client, started, redis, limit_hits):
    redis.limits["VOICE_PREVIEWS_PER_COMPANY_DAY"] = 1
    started.voice["on"] = True

    [preview(client) for _ in range(2)]

    assert [(hit["limit"], hit["company_id"], hit["user_id"]) for hit in limit_hits] == [
        ("VOICE_PREVIEWS_PER_COMPANY_DAY", str(COMPANY_ID), "bob")
    ]


def test_with_redis_down_voice_previews_are_refused_and_others_start(client, started, redis):
    """The voice limit caps spend, so it fails closed; the other only stops floods."""
    redis.down = True

    assert preview(client).status_code == 201

    started.voice["on"] = True

    with pytest.raises(ConnectionError):
        preview(client)

    assert len(started) == 1


def test_a_preview_that_didnt_start_gives_back_its_place_in_the_day(
    client, started, redis, monkeypatch
):
    async def down(payload):
        raise ConnectionError("rounds is down")

    monkeypatch.setattr(rounds, "create_sessions", down)

    with pytest.raises(ConnectionError):
        preview(client)

    assert redis.counts[COMPANY_KEY] == 0


def preview(client):
    return client.post(f"/interviews/{uuid.uuid4()}/preview", json={"pledged": True})


def test_a_preview_of_an_interview_deleted_meanwhile_loses_its_sessions(
    client, started, monkeypatch
):
    """interview.deleted may reach rounds before the preview's sessions do (a delete before a
    create): they're deleted here, and the preview refused."""
    reads = []
    deleted = []

    async def gone_on_second_read(session, interview_id):
        reads.append(interview_id)

        if len(reads) > 1:
            return None

        return Interview(
            id=interview_id,
            company_id=COMPANY_ID,
            generation_id=None,
            set_id=SET_ID,
            question_seconds=45,
            topic_limits={},
        )

    async def delete_invite_sessions(invite_ids):
        deleted.extend(invite_ids)

    monkeypatch.setattr(interviews, "get", gone_on_second_read)
    monkeypatch.setattr(rounds, "delete_invite_sessions", delete_invite_sessions)

    response = client.post(f"/interviews/{uuid.uuid4()}/preview", json={"pledged": True})

    assert response.status_code == 404
    [payload] = started
    assert deleted == [uuid.UUID(payload["candidate_invite_id"])]
