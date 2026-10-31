import time
import uuid
from datetime import datetime, timedelta

from fastapi import status
from testee_common.i18n.i18n import CodedError

from rounds.constants.open_to_offers import (
    CONSENT_OUTDATED,
    CONSENT_OUTDATED_CODE,
    CONSENT_VERSION,
    LINKEDIN_INVALID,
    LINKEDIN_INVALID_CODE,
    OPEN_DAYS,
)
from rounds.core.db import Session
from rounds.helpers.linkedin import linkedin_profile
from rounds.models.open_to_offers import OpenToOffers
from rounds.repositories import open_to_offers
from rounds.schemas.open_to_offers import MatchOut, OpenToOffersOut, PracticeResultOut

# People closed per transaction by the lapse job.
LAPSE_BATCH = 100


def status_out(row: OpenToOffers | None) -> OpenToOffersOut:
    if row is None:
        return OpenToOffersOut(on=False, consent_version=CONSENT_VERSION)

    return OpenToOffersOut(
        on=True,
        name=row.name,
        linkedin_url=row.linkedin_url,
        until=row.opened_at + timedelta(days=OPEN_DAYS),
        consent_version=CONSENT_VERSION,
    )


async def current(user_id: str) -> OpenToOffersOut:
    async with Session() as session:
        return status_out(await open_to_offers.get(session, user_id))


async def turn_on(
    user_id: str, name: str | None, linkedin_url: str, version: str, now: datetime
) -> OpenToOffersOut:
    """Lists the person with their name (their sign-in's) and profile, logging the wording they agreed to; refused for an
    address that isn't a LinkedIn profile's (422) and for wording that's no longer current (409:
    the consent must be to the text in force)."""
    if version != CONSENT_VERSION:
        raise CodedError(status.HTTP_409_CONFLICT, CONSENT_OUTDATED, CONSENT_OUTDATED_CODE)

    profile = linkedin_profile(linkedin_url)

    if profile is None:
        raise CodedError(
            status.HTTP_422_UNPROCESSABLE_CONTENT, LINKEDIN_INVALID, LINKEDIN_INVALID_CODE
        )

    async with Session.begin() as session:
        await open_to_offers.save(session, user_id, name, profile, now)
        await open_to_offers.log(session, [user_id], True, CONSENT_VERSION)
        row = await open_to_offers.get(session, user_id)

    return status_out(row)


async def turn_off(user_id: str) -> None:
    """Takes the person off every Discover tab at once; logged only when they were on them, so
    turning it off again changes nothing."""
    async with Session.begin() as session:
        closed = await open_to_offers.close(session, [user_id])
        await open_to_offers.log(session, closed, False, None)


async def close_lapsed(now: datetime, deadline: float) -> None:
    """Daily: closes the opt-ins turned on more than OPEN_DAYS ago, a batch a transaction, until
    none is left or `deadline` (time.monotonic) passes; the next run takes the rest."""
    before = now - timedelta(days=OPEN_DAYS)

    while time.monotonic() < deadline:
        async with Session.begin() as session:
            found = await open_to_offers.lapsed(session, before, LAPSE_BATCH)
            closed = await open_to_offers.close(session, found)
            await open_to_offers.log(session, closed, False, None)

        if len(found) < LAPSE_BATCH:
            return


async def matches(topic_ids: list[uuid.UUID], offset: int, limit: int) -> list[MatchOut]:
    """The listed people with practice results on these topics, a page at a time."""
    if not topic_ids:
        return []

    async with Session() as session:
        people, results = await open_to_offers.matches(session, topic_ids, offset, limit)

    return [
        MatchOut(
            user_id=person.user_id,
            name=person.name,
            linkedin_url=person.linkedin_url,
            results=[
                PracticeResultOut(
                    topic_title=row.topic_title, score=row.final_score, finished_at=row.finished_at
                )
                for row in results
                if row.user_id == person.user_id
            ],
        )
        for person in people
    ]
