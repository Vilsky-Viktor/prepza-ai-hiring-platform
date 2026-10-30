"""Open to offers: the switch's saves and consent log, what companies' Discover tab gets, and
that turning it off, a lapse or deleting the account takes the person off at once
(services/open_to_offers.py)."""

import time
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import update

from rounds.constants.open_to_offers import CONSENT_VERSION, OPEN_DAYS
from rounds.constants.rounds import RoundStatus
from rounds.models.sessions import Session as RoundSession
from rounds.services import accounts, open_to_offers
from tests.integration import factories
from tests.integration.transactions import transaction

NOW = datetime(2026, 10, 30, 12, tzinfo=UTC)
PROFILE = "https://www.linkedin.com/in/{}"


async def finished(user_id, topic, score, at, seconds=60):
    """A finished practice section on `topic` with this grade, finished at `at`; untimed
    without `seconds`."""
    [row] = await factories.created(user_id, uuid.uuid4(), [topic], seconds, practice=True)

    async def finish(session):
        await session.execute(
            update(RoundSession)
            .where(RoundSession.id == row.id)
            .values(status=RoundStatus.FINISHED, final_score=score, finished_at=at)
        )

    await transaction(finish)


async def opened(user_id, at=NOW):
    return await open_to_offers.turn_on(
        user_id, f"Name {user_id}", f"linkedin.com/in/{user_id}", CONSENT_VERSION, at
    )


def person(user_id, *results):
    return {
        "user_id": user_id,
        "name": f"Name {user_id}",
        "linkedin_url": PROFILE.format(user_id),
        "results": [{"topic_title": "Python", "score": s, "finished_at": a} for s, a in results],
    }


def listed(found):
    return [match.model_dump() for match in found]


def test_companies_get_only_open_people_with_their_latest_timed_results_last_practice_first(run):
    topic, elsewhere = factories.topic(), factories.topic()
    ann, bob, cid, dan = (f"{name}-{uuid.uuid4().hex[:6]}" for name in ("ann", "bob", "cid", "dan"))

    async def scenario():
        await finished(ann, topic, 40, NOW - timedelta(days=5))
        await finished(ann, topic, 80, NOW - timedelta(days=3))
        await finished(bob, topic, 60, NOW - timedelta(days=1))
        # Untimed practice measures nothing, and another subject's results don't count.
        await finished(bob, topic, 100, NOW, seconds=None)
        await finished(bob, elsewhere, 90, NOW)
        # Not open to offers: never listed, whatever their results.
        await finished(cid, topic, 100, NOW)
        # Open, with no result on the subject.
        await finished(dan, elsewhere, 100, NOW)

        for user_id in (ann, bob, dan):
            await opened(user_id)

        return (
            await open_to_offers.matches([topic.id], 0, 10),
            await open_to_offers.matches([topic.id], 1, 1),
            await open_to_offers.matches([], 0, 10),
        )

    everyone, second_page, no_topics = run(scenario())

    assert listed(everyone) == [
        person(bob, (60, NOW - timedelta(days=1))),
        person(ann, (80, NOW - timedelta(days=3))),
    ]
    assert [match.user_id for match in second_page] == [ann]
    assert no_topics == []


def test_turning_it_off_lapsing_or_deleting_the_account_takes_them_off_at_once(run):
    topic = factories.topic()
    off, lapsing, kept, deleted = (f"u-{uuid.uuid4().hex[:8]}" for _ in range(4))

    async def scenario():
        for user_id in (off, lapsing, kept, deleted):
            await finished(user_id, topic, 70, NOW)

        await opened(lapsing, NOW - timedelta(days=OPEN_DAYS + 1))

        for user_id in (off, kept, deleted):
            await opened(user_id)

        await open_to_offers.turn_off(off)
        # Again changes nothing, and logs nothing more.
        await open_to_offers.turn_off(off)
        await open_to_offers.close_lapsed(NOW, time.monotonic() + 30)
        await accounts.remove_user(deleted)
        await accounts.remove_user(deleted)

        return (
            await open_to_offers.matches([topic.id], 0, 10),
            await open_to_offers.current(off),
            await accounts.export_user(off),
            await accounts.export_user(lapsing),
            await accounts.export_user(deleted),
        )

    found, current, off_export, lapsed_export, deleted_export = run(scenario())

    assert [match.user_id for match in found] == [kept]
    assert (current.on, current.linkedin_url) == (False, None)
    assert off_export["open_to_offers"] is None
    assert [(c["on"], c["wording_version"]) for c in off_export["open_to_offers_changes"]] == [
        (True, CONSENT_VERSION),
        (False, None),
    ]
    assert [c["on"] for c in lapsed_export["open_to_offers_changes"]] == [True, False]
    assert deleted_export["open_to_offers"] is None
    assert deleted_export["open_to_offers_changes"] == []
    assert deleted_export["interview_sections"] == []


def test_turning_it_on_again_renews_it_with_the_new_profile_and_logs_each_consent(run):
    user_id = f"u-{uuid.uuid4().hex[:8]}"

    async def scenario():
        await opened(user_id, NOW - timedelta(days=10))
        renewed = await open_to_offers.turn_on(
            user_id, "Ann", "https://uk.linkedin.com/in/ann-new/", CONSENT_VERSION, NOW
        )

        return renewed, await accounts.export_user(user_id)

    renewed, export = run(scenario())

    assert (renewed.on, renewed.name, renewed.linkedin_url) == (
        True,
        "Ann",
        "https://www.linkedin.com/in/ann-new",
    )
    assert renewed.until == NOW + timedelta(days=OPEN_DAYS)
    assert export["open_to_offers"]["linkedin_url"] == "https://www.linkedin.com/in/ann-new"
    assert [c["on"] for c in export["open_to_offers_changes"]] == [True, True]
