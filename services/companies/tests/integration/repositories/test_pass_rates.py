import uuid

from companies.repositories import interviews, invite_progress, link_invites, pass_rates
from companies.schemas.interviews import InterviewSettings
from tests.integration import factories
from tests.integration.transactions import transaction


async def interview(grades, pass_mark=60, unfinished=0):
    """A company's interview whose candidates finished with `grades`, and `unfinished` more."""
    company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
    found = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
    await transaction(interviews.update_settings, found.id, InterviewSettings(pass_mark=pass_mark))

    for index, grade in enumerate(grades):
        invite = await transaction(link_invites.for_link, found.id, f"c{index}@example.com")
        await transaction(invite_progress.finish, invite.id, grade, False, None)

    for index in range(unfinished):
        await transaction(link_invites.for_link, found.id, f"u{index}@example.com")

    return found.id


def mine(rows, ids):
    return [(row.finished, row.passed, float(row.average)) for row in rows if row.id in ids]


def test_rates_count_only_finished_candidates_against_each_pass_mark_sorted_in_sql(run):
    async def scenario():
        # Passed at or above the mark: 2 of 3, 1 of 2 (mark 50), none of 1.
        most = await interview([60, 59, 90], unfinished=2)
        half = await interview([50, 40], pass_mark=50)
        none = await interview([10])
        never = await interview([], unfinished=1)
        ids = [most, half, none, never]

        return (
            mine(await transaction(pass_rates.page, False, None, 1000), ids),
            mine(await transaction(pass_rates.page, True, None, 1000), ids),
        )

    by_rate, by_finished = run(scenario())

    # Lowest pass rate first; an interview nobody finished isn't listed.
    assert by_rate == [(1, 0, 10.0), (2, 1, 45.0), (3, 2, 69.66666666666667)]
    # Most finished first.
    assert [row[0] for row in by_finished] == [3, 2, 1]


async def session_company(interview_id):
    from companies.repositories.interviews import get

    return (await transaction(get, interview_id)).company_id


def test_the_counters_match_a_recount_after_finishes_grades_removals_and_a_new_mark(run):
    from sqlalchemy import func, select

    from companies.constants.invites import InviteStatus
    from companies.core.db import Session
    from companies.models.interview_results import InterviewResult
    from companies.models.interviews import Interview
    from companies.models.invites import CandidateInvite
    from companies.repositories import candidates, invites

    async def scenario():
        found = await interview([60, 59, 90], unfinished=1)
        [first, *_] = await transaction(candidates.for_report, found, 0, 10)
        # A grade written again, a candidate removed, the pass mark changed.
        await transaction(candidates.save_results, {first.id: (95, False)})
        [removed] = [
            row for row in await transaction(candidates.for_report, found, 0, 10) if row.grade == 59
        ]
        company_id = await session_company(found)
        await transaction(invites.remove, removed, company_id)
        await transaction(interviews.update_settings, found, InterviewSettings(pass_mark=80))

        async with Session() as session:
            kept = await session.get(InterviewResult, found)
            mark = await session.scalar(select(Interview.pass_mark).where(Interview.id == found))
            recount = (
                await session.execute(
                    select(
                        func.count(),
                        func.count().filter(CandidateInvite.grade >= mark),
                        func.sum(CandidateInvite.grade),
                    ).where(
                        CandidateInvite.interview_id == found,
                        CandidateInvite.status == InviteStatus.FINISHED,
                        CandidateInvite.grade.is_not(None),
                    )
                )
            ).one()

        return (kept.finished, kept.passed, kept.grade_total), tuple(recount)

    kept, recount = run(scenario())

    assert kept == recount


def test_pass_rates_page_by_key_after_the_last_one_shown(run):
    async def scenario():
        ids = [await interview([grade]) for grade in (10, 20, 30)]
        first = [
            row for row in await transaction(pass_rates.page, False, None, 1000) if row.id in ids
        ][:2]
        rest = await transaction(pass_rates.page, False, first[-1].id, 1000)

        return ids, [row.id for row in first], [row.id for row in rest if row.id in ids]

    ids, first, rest = run(scenario())

    # Lowest pass rate first (all 0 of 1, then by id); the page after the second has the third.
    assert first + rest == sorted(ids)
