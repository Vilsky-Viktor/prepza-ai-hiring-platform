"""A report's candidates and a company's interviews are read a batch at a time."""

import uuid

from app.storage import candidates, companies, interviews, invites


def test_a_reports_candidates_come_in_batches_best_grade_first(run):
    async def scenario():
        company = await companies.create(f"Batches {uuid.uuid4()}", "owner", "o@example.com")
        interview = await interviews.create(company.id, uuid.uuid4(), "en", 60)

        for name in ("ann", "bob", "cid"):
            await invites.upsert(interview.id, f"{name}@example.com", "Backend", "Acme", "en")

        first = await candidates.for_report(interview.id, 0, 2)
        rest = await candidates.for_report(interview.id, 2, 2)

        return len(first), len(rest), {row.id for row in first} & {row.id for row in rest}

    assert run(scenario()) == (2, 1, set())


def test_a_companys_interviews_come_a_page_at_a_time_by_id(run):
    async def scenario():
        company = await companies.create(f"Pages {uuid.uuid4()}", "owner", "o@example.com")
        made = sorted(
            [(await interviews.create(company.id, uuid.uuid4(), "en", 60)).id for _ in range(3)]
        )
        first = await interviews.page_by_id(company.id, None, 2)
        second = await interviews.page_by_id(company.id, first[-1].id, 2)

        return made, [row.id for row in first + second]

    made, read = run(scenario())

    assert read == made
