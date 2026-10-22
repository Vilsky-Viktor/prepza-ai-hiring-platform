import uuid

from app.constants.invites import NOT_STARTED, STARTED
from app.helpers.candidate_lists import read_list
from app.storage import accounts, candidates, companies, interviews, invite_progress, invites


async def invited(email: str):
    company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
    interview = await interviews.create(company.id, uuid.uuid4(), "en", 60)
    invite, _ = await invites.upsert(interview.id, email, "Backend", "Acme", "en")

    return interview, invite


def test_the_sign_in_fills_a_candidates_name_once_and_never_overwrites_it(run):
    async def scenario():
        interview, invite = await invited("maria@example.com")
        before = await candidates.get(interview.id, invite.id)
        await invite_progress.start(invite.id, "maria-uid", "Maria Kowalska")
        filled = await candidates.get(interview.id, invite.id)
        # Starting again, with another name in the sign-in, keeps the first.
        await invite_progress.start(invite.id, "maria-uid", "mk")
        kept = await candidates.get(interview.id, invite.id)

        return before.name, filled.name, kept.name

    assert run(scenario()) == (None, "Maria Kowalska", "Maria Kowalska")


def test_a_sign_in_without_a_name_leaves_it_unknown(run):
    async def scenario():
        interview, invite = await invited("noname@example.com")
        await invite_progress.start(invite.id, "noname-uid", None)

        return (await candidates.get(interview.id, invite.id)).name

    assert run(scenario()) is None


def test_a_name_an_owner_set_survives_the_sign_in_and_blank_makes_it_unknown(run):
    async def scenario():
        interview, invite = await invited("nick@example.com")
        await invite_progress.start(invite.id, "nick-uid", "nick99")
        await invites.change(invite.id, {"name": "Nicholas Brown"}, STARTED)
        await invite_progress.start(invite.id, "nick-uid", "nick99")
        corrected = (await candidates.get(interview.id, invite.id)).name
        await invites.change(invite.id, {"name": None}, STARTED)
        cleared = (await candidates.get(interview.id, invite.id)).name

        return corrected, cleared

    assert run(scenario()) == ("Nicholas Brown", None)


def test_a_deleted_account_takes_its_name_with_it_and_an_export_holds_it(run):
    async def scenario():
        interview, invite = await invited("gone-name@example.com")
        await invite_progress.start(invite.id, "gone-name-uid", "Gone Person")
        exported = await accounts.export("gone-name-uid", "gone-name@example.com")
        await accounts.forget_candidate("gone-name-uid", "gone-name@example.com")

        return exported, (await candidates.get(interview.id, invite.id)).name

    exported, after = run(scenario())

    assert [row["name"] for row in exported["interview_invites"]] == ["Gone Person"]
    assert after is None


def test_an_inviters_name_fills_an_unknown_name_and_a_known_one_stays(run):
    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await interviews.create(company.id, uuid.uuid4(), "en", 60)
        invite, _ = await invites.upsert(interview.id, "x@example.com", "B", "A", "en", name="Xi")
        # Sent again (a redelivered ATS candidate, a list pasted again): an edit stays.
        await invites.change(invite.id, {"name": "Xi Jun"}, NOT_STARTED)
        await invites.upsert(interview.id, "x@example.com", "B", "A", "en", name="Xi")
        await invite_progress.start(invite.id, "x-uid", "Signed In Name")

        return (await candidates.get(interview.id, invite.id)).name

    assert run(scenario()) == "Xi Jun"


def test_candidates_are_found_by_part_of_their_name_or_email_in_any_case(run):
    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await interviews.create(company.id, uuid.uuid4(), "en", 60)
        await invites.upsert(interview.id, "maria@example.com", "B", "A", "en", name="Maria Ruiz")
        await invites.upsert(interview.id, "ruiz.j@example.com", "B", "A", "en")
        await invites.upsert(interview.id, "other@example.com", "B", "A", "en")

        async def emails(q):
            rows = await candidates.page(interview.id, 0, 10, False, q)

            return sorted(row.email for row in rows)

        return await emails("RUIZ"), await emails("maria"), await emails("nobody")

    by_both, by_name_or_email, none = run(scenario())

    assert by_both == ["maria@example.com", "ruiz.j@example.com"]
    assert by_name_or_email == ["maria@example.com"]
    assert none == []


def test_a_csv_lists_names_are_stored_with_its_invites(run):
    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        interview = await interviews.create(company.id, uuid.uuid4(), "en", 60)
        text = "Vorname;Nachname;E-Mail\nAnn;Lee;ann@example.com\n;;bob@example.com\n"

        for email, name in read_list(text)[0]:
            await invites.upsert(interview.id, email, "B", "A", "en", name=name)

        rows = await candidates.page(interview.id, 0, 10, False)

        return sorted((row.email, row.name) for row in rows)

    assert run(scenario()) == [("ann@example.com", "Ann Lee"), ("bob@example.com", None)]


def test_a_candidates_changes_are_written_together_or_not_at_all(run):
    """A change allowed only before the start writes nothing, its name included, for one who
    started."""

    async def scenario():
        _, invite = await invited(f"both-{uuid.uuid4().hex[:8]}@example.com")
        written = await invites.change(invite.id, {"name": "Ann", "extra_time": 25}, NOT_STARTED)
        await invite_progress.start(invite.id, f"u-{invite.id}")
        refused = await invites.change(invite.id, {"name": "Bo", "extra_time": 50}, NOT_STARTED)
        found = await invites.get(invite.id)

        return written, refused, found.name, found.extra_time

    assert run(scenario()) == (True, False, "Ann", 25)
