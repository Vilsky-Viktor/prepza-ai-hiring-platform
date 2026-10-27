import uuid

import pytest
from fastapi import HTTPException
from prepza_common.limits import limits
from prepza_common.limits.rate_limit import hit_emails
from redis.asyncio import Redis

from app.config.settings import settings

TOO_MANY_REQUESTS = "Too many requests. Try again later."


def test_email_limits_count_in_real_redis(run, monkeypatch):
    sender = f"sender-{uuid.uuid4()}"
    company_id = uuid.uuid4()
    hits = []

    async def recorded(event_type, data, attempts, timeout):
        hits.append(data)

    monkeypatch.setattr(limits, "publish_retried", recorded)

    async def scenario():
        redis = Redis.from_url(settings.redis_url)

        try:
            # One address gets at most 3 invites to the same thing a day (the limit's default).
            for _ in range(3):
                await hit_emails(redis, sender, "interview:carol@example.com", company_id)

            with pytest.raises(HTTPException) as refused:
                await hit_emails(redis, sender, "interview:carol@example.com", company_id)

            ttl = await redis.ttl("rate:emails:recipient:interview:carol@example.com")
            await redis.delete(
                f"rate:emails:hour:{sender}",
                f"rate:emails:day:{sender}",
                "rate:emails:recipient:interview:carol@example.com",
            )
        finally:
            await redis.aclose()

        return refused.value, ttl

    refusal, ttl = run(scenario())

    assert (refusal.status_code, refusal.detail) == (429, TOO_MANY_REQUESTS)
    # Every counter expires, so a limit never sticks forever.
    assert 0 < ttl <= 24 * 60 * 60
    # The refusal says when the window ends.
    assert 0 < int(refusal.headers["Retry-After"]) <= 24 * 60 * 60
    assert [(hit["limit"], hit["company_id"], hit["user_id"]) for hit in hits] == [
        ("EMAIL_RECIPIENT_DAILY_LIMIT", str(company_id), sender)
    ]


def test_invites_refused_for_credits_use_up_no_email_limits(run, monkeypatch):
    """A company out of credits (an ATS sending candidates) must not use up the limits, or its
    invites are refused with 429 once it tops up."""
    from prepza_common.auth.user import User

    from app.integrations import billing
    from app.services import candidate_invites
    from app.storage import companies, interview_generations, interviews

    credits = {"left": False}

    async def hold(company_id, key):
        if not credits["left"]:
            raise HTTPException(402, "No candidate credits left.")

    monkeypatch.setattr(billing, "hold_candidate", hold)
    sender = User(uid=f"sender-{uuid.uuid4()}", email="", email_verified=True)
    email = "dana@example.com"

    async def scenario():
        redis = Redis.from_url(settings.redis_url)
        monkeypatch.setattr(candidate_invites, "get_redis", lambda: redis)
        company = await companies.create(f"Acme {uuid.uuid4()}", sender.uid, "o@example.com")
        created = await interviews.create(company.id, uuid.uuid4(), "en", 60)
        await interview_generations.set_set_id(created.id, uuid.uuid4())
        # Titled, so nothing asks library for it.
        await interviews.set_title(created.id, "Backend interview")
        interview = await interviews.get(created.id)
        codes = []

        try:
            for left in (False,) * 4 + (True,) * 3:
                credits["left"] = left

                try:
                    await candidate_invites.invite(interview, company, sender, email)
                    codes.append(201)
                except HTTPException as error:
                    codes.append(error.status_code)

            await redis.delete(
                f"rate:emails:hour:{sender.uid}",
                f"rate:emails:day:{sender.uid}",
                f"rate:emails:recipient:{interview.id}:{email}",
            )
        finally:
            await redis.aclose()

        return codes

    assert run(scenario()) == [402] * 4 + [201] * 3
