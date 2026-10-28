import uuid
from datetime import UTC, datetime, timedelta

from companies.constants.invites import NOT_STARTED
from companies.repositories import candidates, companies, interviews, invites


def test_a_changed_candidate_comes_last_and_a_cursor_never_repeats_or_skips_one(run):
    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        found = await interviews.create(company.id, uuid.uuid4(), "en", 60)
        since = datetime.now(UTC) - timedelta(seconds=1)
        made = []

        for email in ("ann@example.com", "ben@example.com", "cid@example.com"):
            invite, _ = await invites.upsert(found.id, email, "Backend", "Acme", "en")
            made.append(invite)

        # Ann changes after the others were invited: the trigger moves her to the end.
        await invites.change(made[0].id, {"name": "Ann Lee"}, NOT_STARTED)

        def page(since, after=None):
            return candidates.page(found.id, 0, 2, False, since=since, after=after)

        first = await page(since)
        # The next page starts after the last one got: its time and id.
        rest = await page(first[-1].updated_at, first[-1].id)
        later = await candidates.page(
            found.id, 0, 10, False, since=datetime.now(UTC) + timedelta(minutes=1)
        )
        renamed = await candidates.get(found.id, made[0].id)

        return made, first, rest, later, renamed

    made, first, rest, later, renamed = run(scenario())
    emails = [invite.email for invite in first + rest]

    assert emails == ["ben@example.com", "cid@example.com", "ann@example.com"]
    assert later == []
    assert renamed.updated_at > made[0].updated_at


def test_an_interview_changed_since_is_listed_oldest_change_first(run):
    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        since = datetime.now(UTC) - timedelta(seconds=1)
        older = await interviews.create(company.id, uuid.uuid4(), "en", 60)
        newer = await interviews.create(company.id, uuid.uuid4(), "en", 60)
        await interviews.set_title(older.id, "Renamed")
        listed = await interviews.list_for_company(company.id, 0, 10, since)

        return [row.id for row in listed], older.id, newer.id

    listed, older, newer = run(scenario())

    assert listed == [newer, older]


def test_interviews_are_found_by_part_of_their_title_in_any_case(run):
    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        sql = await interviews.create(company.id, uuid.uuid4(), "en", 60)
        await interviews.set_title(sql.id, "Backend SQL_Basics")
        other = await interviews.create(company.id, uuid.uuid4(), "en", 60)
        await interviews.set_title(other.id, "Designer")
        found = await interviews.list_for_company(company.id, 0, 10, q="sql_b")
        underscore = await interviews.list_for_company(company.id, 0, 10, q="l_b")

        return [row.id for row in found], [row.id for row in underscore], sql.id

    found, underscore, sql = run(scenario())

    assert found == [sql]
    # An underscore is matched as typed, not as any character.
    assert underscore == [sql]
