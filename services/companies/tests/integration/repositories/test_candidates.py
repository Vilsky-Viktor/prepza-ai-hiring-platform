import uuid
from datetime import UTC, datetime, timedelta

from companies.constants.invites import CandidateFilter, InviteStatus
from companies.repositories import (
    candidates,
    interviews,
    invite_expiry,
    invite_progress,
    invites,
    link_invites,
)
from companies.services import accounts as account_service
from tests.integration import factories
from tests.integration.transactions import transaction


async def interview():
    company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")

    return await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)


async def invite(found, email):
    invite, _ = await transaction(invites.upsert, found.id, email, "Backend", "Acme", "en")

    return invite


def emails(rows):
    return [row.email for row in rows]


def test_candidates_are_found_by_part_of_their_email_and_by_status(run):
    async def scenario():
        found = await interview()

        for email in ("ann_lee@example.com", "annlee@example.com", "bob@example.com"):
            await invite(found, email)

        bob = await transaction(link_invites.for_link, found.id, "bob@example.com")
        await transaction(invite_progress.finish, bob.id, 50, False, None)

        return (
            sorted(emails(await transaction(candidates.page, found.id, 0, 10, False, "ANN"))),
            emails(await transaction(candidates.page, found.id, 0, 10, False, "ann_")),
            emails(
                await transaction(
                    candidates.page, found.id, 0, 10, False, "", InviteStatus.FINISHED
                )
            ),
        )

    by_text, underscore, finished = run(scenario())

    assert by_text == ["ann_lee@example.com", "annlee@example.com"]
    # An underscore is matched as typed, not as any character.
    assert underscore == ["ann_lee@example.com"]
    assert finished == ["bob@example.com"]


def test_candidates_sort_by_stored_grade_filter_by_result_and_page_in_sql(run):
    async def scenario():
        found = await interview()
        # Invited in this order, so newest first is cleo, ben, ada, dan.
        dan = await invite(found, "dan@example.com")
        ada = await invite(found, "ada@example.com")
        ben = await invite(found, "ben@example.com")
        await invite(found, "cleo@example.com")
        await transaction(invite_progress.finish, ada.id, 90, True, None)
        await transaction(invite_progress.finish, ben.id, 60, False, None)
        await transaction(invite_progress.finish, dan.id, 75, False, None)

        def listed(offset, limit, filter_by=None):
            return transaction(candidates.page, found.id, offset, limit, True, "", filter_by, 70)

        return (
            emails(await listed(0, 2)) + emails(await listed(2, 2)),
            emails(await listed(0, 10, CandidateFilter.PASSED)),
            emails(await listed(0, 10, CandidateFilter.FLAGGED)),
        )

    by_grade, passed, flagged = run(scenario())

    # Best grade first; cleo, still to finish, comes last.
    assert by_grade == [
        "ada@example.com",
        "dan@example.com",
        "ben@example.com",
        "cleo@example.com",
    ]
    assert passed == ["ada@example.com", "dan@example.com"]
    assert flagged == ["ada@example.com"]


def test_lookups_count_find_one_candidate_and_leave_out_deleted_ones(run):
    async def scenario():
        found = await interview()
        other = await interview()
        ann = await invite(found, "ann@example.com")
        gone = await invite(found, "gone@example.com")
        await transaction(invite_progress.start, gone.id, "gone-uid")
        await account_service.forget("gone-uid", "gone@example.com", [])
        before_finish = await transaction(candidates.any_finished, found.id)
        await transaction(invite_progress.finish, ann.id, None, False, None)

        return (
            await transaction(candidates.counts, [found.id, other.id]),
            await transaction(candidates.get, found.id, ann.id),
            await transaction(candidates.get, other.id, ann.id),
            before_finish,
            await transaction(candidates.any_finished, found.id),
            await transaction(candidates.unscored, found.id),
            emails(await transaction(candidates.for_report, found.id, 0, 1000)),
            found.id,
            ann.id,
        )

    counts, mine, elsewhere, before, after, unscored, report, found_id, ann_id = run(scenario())

    # The deleted account's invite is gone, not kept as a row.
    assert counts == {found_id: 1}
    assert mine.id == ann_id
    assert elsewhere is None
    assert (before, after) == (False, True)
    # Finished without a grade (rounds didn't answer): the list stores it later.
    assert unscored == [ann_id]
    assert report == ["ann@example.com"]


def test_results_saved_from_the_list_keep_the_status_for_the_finish_event(run):
    async def scenario():
        found = await interview()
        ann = await invite(found, "ann@example.com")
        await transaction(invite_progress.start, ann.id, "ann-uid")
        await transaction(candidates.save_results, {ann.id: (85, True)})

        return await transaction(invites.get, ann.id)

    saved = run(scenario())

    # Only interview.finished marks it finished, as it settles the credits.
    assert (saved.status, saved.grade, saved.flagged) == (InviteStatus.IN_PROCESS, 85, True)


def test_an_expired_invite_started_through_the_link_is_in_process(run):
    async def scenario():
        found = await interview()
        ann = await invite(found, "ann@example.com")
        later = datetime.now(UTC) + timedelta(seconds=1)
        await transaction(invite_expiry.mark_expired, ann.id, later)
        before = await transaction(invite_progress.start, ann.id, "ann-uid")

        return (
            before,
            await transaction(invites.get, ann.id),
            await transaction(invite_progress.start, uuid.uuid4(), "nobody"),
        )

    before, started, missing = run(scenario())

    assert (started.status, started.user_id) == (InviteStatus.IN_PROCESS, "ann-uid")
    # Its status before, so its credits are set aside again.
    assert before == InviteStatus.EXPIRED
    # An invite revoked meanwhile isn't started.
    assert missing is None


def test_sending_an_expired_invite_again_says_it_revived_it(run):
    async def scenario():
        found = await interview()
        ann = await invite(found, "ann@example.com")
        _, fresh = await transaction(
            invites.upsert, found.id, "ann@example.com", "Backend", "Acme", "en"
        )
        later = datetime.now(UTC) + timedelta(seconds=1)
        await transaction(invite_expiry.mark_expired, ann.id, later)
        _, revived = await transaction(
            invites.upsert, found.id, "ann@example.com", "Backend", "Acme", "en"
        )

        return fresh, revived, (await transaction(invites.get, ann.id)).status

    # Only an expired one: its credits were given back, so they're set aside again.
    assert run(scenario()) == (False, True, InviteStatus.INVITED)


def test_an_invite_sent_again_while_expiring_isnt_expired(run):
    async def scenario():
        found = await interview()
        ann = await invite(found, "ann@example.com")
        cutoff = datetime.now(UTC)
        # Sent again after the run read it: its new send is after the cutoff.
        await invite(found, "ann@example.com")
        resent = await transaction(invite_expiry.mark_expired, ann.id, cutoff)

        bob = await invite(found, "bob@example.com")
        later = datetime.now(UTC) + timedelta(seconds=1)
        expired = await transaction(invite_expiry.mark_expired, bob.id, later)

        return resent, expired

    assert run(scenario()) == (False, True)


def test_only_stale_unstarted_invites_are_expiring_and_marking_one_expires_it(run):
    async def scenario():
        found = await interview()
        stale, _ = await transaction(
            invites.upsert, found.id, "old@example.com", "Backend", "Acme", "en"
        )
        await transaction(invites.upsert, found.id, "new@example.com", "Backend", "Acme", "en")
        later = datetime.now(UTC) + timedelta(seconds=1)
        due = [
            row.email
            for row in await transaction(invite_expiry.expiring, later, 500)
            if row.interview_id == found.id
        ]
        await transaction(invite_expiry.mark_expired, stale.id, later)
        after = [
            row.email
            for row in await transaction(invite_expiry.expiring, later, 500)
            if row.interview_id == found.id
        ]

        return due, after, (await transaction(invites.get, stale.id)).status

    due, after, status = run(scenario())

    assert sorted(due) == ["new@example.com", "old@example.com"]
    assert after == ["new@example.com"]
    assert status == InviteStatus.EXPIRED
