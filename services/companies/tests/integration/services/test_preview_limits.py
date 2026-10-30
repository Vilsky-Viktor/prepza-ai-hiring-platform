"""A company's previews a day, counted in real Redis: voice mode's apart from the others, per
company, the values edited in the admin zone, and a new day once the window ends."""

import uuid

import pytest
from fastapi import HTTPException
from prepza_common.limits.limit_list import LIMITS_KEY
from redis.asyncio import Redis

from companies.config import settings
from companies.constants.interviews import PREVIEWS_USED_UP, VOICE_PREVIEWS_USED_UP
from companies.integrations import library, rounds
from companies.repositories import interview_generations, interviews
from companies.services import previews
from tests.integration import factories
from tests.integration.transactions import transaction

DAY = 24 * 60 * 60
# Long enough for the key's expiry to be seen, short enough not to wait on.
EXPIRY_POLLS = 200


@pytest.fixture
def ready(monkeypatch):
    """Library's questions and rounds' sessions answered in memory; returns what rounds was
    asked to start."""
    started = []

    async def content(_set_id):
        questions = [{"id": str(uuid.uuid4()), "text": "Q?", "options": []} for _ in range(3)]

        return {
            "id": str(uuid.uuid4()),
            "topics": [{"id": "t", "title": "SQL", "questions": questions}],
        }

    async def create_sessions(payload):
        started.append(payload)

        return [{"id": str(uuid.uuid4())}]

    monkeypatch.setattr(library, "get_content", content)
    monkeypatch.setattr(rounds, "create_sessions", create_sessions)

    return started


async def ready_interview(voice: bool = False):
    """A company of its own with one ready interview, taken by voice when `voice`."""
    owner = f"owner-{uuid.uuid4()}"
    company = await factories.company(f"Acme {uuid.uuid4()}", owner, "o@example.com")
    created = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
    await transaction(interview_generations.set_set_id, created.id, uuid.uuid4())
    await transaction(interviews.set_title, created.id, "Backend interview")
    interview = await transaction(interviews.get, created.id)
    interview.voice = voice

    return interview, owner


async def outcomes(interview, user_id: str, times: int) -> list:
    """201 for each preview started, the refusal for each one refused."""
    found = []

    for _ in range(times):
        try:
            await previews.preview(interview, user_id)
            found.append(201)
        except HTTPException as error:
            found.append(error)

    return found


def test_voice_and_other_previews_are_limited_per_company_and_apart(run, ready, monkeypatch):
    async def scenario():
        redis = Redis.from_url(settings.redis_url)
        monkeypatch.setattr(previews, "get_redis", lambda: redis)

        try:
            voice, owner = await ready_interview(voice=True)
            clicks, _ = await ready_interview()
            other, other_owner = await ready_interview(voice=True)
            clicks.company_id = voice.company_id

            return (
                await outcomes(voice, owner, 6),
                # The same company's other previews and another company's still start.
                await outcomes(clicks, owner, 1),
                await outcomes(other, other_owner, 1),
                await redis.ttl(f"rate:previews:voice:{voice.company_id}"),
            )
        finally:
            await redis.aclose()

    voice, clicks, other, ttl = run(scenario())

    assert voice[:5] == [201] * 5
    refusal = voice[5]
    assert (refusal.status_code, refusal.detail) == (
        429,
        VOICE_PREVIEWS_USED_UP.format(limit=5, hours=24),
    )
    assert 0 < int(refusal.headers["Retry-After"]) <= DAY
    assert clicks == [201]
    assert other == [201]
    assert 0 < ttl <= DAY
    assert len(ready) == 7


def test_the_admin_zones_value_holds_and_a_new_window_starts_afresh(run, ready, monkeypatch):
    async def scenario():
        redis = Redis.from_url(settings.redis_url)
        monkeypatch.setattr(previews, "get_redis", lambda: redis)

        try:
            await redis.hset(LIMITS_KEY, mapping={"PREVIEWS_PER_COMPANY_DAY": 2})
            interview, owner = await ready_interview()
            before = await outcomes(interview, owner, 3)
            # The window ends: Redis drops the counter, as it does after a day.
            key = f"rate:previews:company:{interview.company_id}"
            await redis.pexpire(key, 1)

            for _ in range(EXPIRY_POLLS):
                if not await redis.exists(key):
                    break

            after = await outcomes(interview, owner, 1)
        finally:
            await redis.hdel(LIMITS_KEY, "PREVIEWS_PER_COMPANY_DAY")
            await redis.aclose()

        return before, after

    before, after = run(scenario())

    assert before[:2] == [201, 201]
    assert (before[2].status_code, before[2].detail) == (
        429,
        PREVIEWS_USED_UP.format(limit=2, hours=24),
    )
    assert after == [201]
