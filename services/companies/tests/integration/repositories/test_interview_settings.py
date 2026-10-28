import uuid

from companies.repositories import interview_generations, interviews
from companies.schemas.interviews import InterviewSettings
from tests.integration import factories
from tests.integration.transactions import transaction


def test_saving_one_setting_keeps_the_others(run):
    async def scenario():
        company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        found = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
        await transaction(
            interviews.update_settings,
            found.id,
            InterviewSettings(question_seconds=45, pass_mark=85),
        )
        await transaction(interviews.update_settings, found.id, InterviewSettings(hired=True))

        return await transaction(interviews.get, found.id)

    saved = run(scenario())

    assert (saved.question_seconds, saved.pass_mark, saved.hired) == (45, 85, True)


def test_a_new_tests_questions_are_shared_until_the_company_keeps_them_out(run):
    async def scenario():
        company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        found = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
        new = (await transaction(interviews.get, found.id)).keep_private
        await transaction(
            interviews.update_settings, found.id, InterviewSettings(keep_private=True)
        )
        kept = await transaction(interviews.get, found.id)
        await transaction(
            interviews.update_settings, found.id, InterviewSettings(keep_private=False)
        )

        return (
            new,
            kept.keep_private,
            kept.hired,
            (await transaction(interviews.get, found.id)).keep_private,
        )

    # Off when made, as the terms say; on and off again leaves the other settings alone.
    assert run(scenario()) == (False, True, False, False)


def test_a_generated_test_takes_its_levels_seconds_once_and_keeps_the_companys_after(run):
    """The first completion gives the level's seconds; a later one (a retried event, a
    regeneration) keeps what the company set since; one without a level keeps the test's."""

    async def scenario():
        company = await factories.company(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        found = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
        old = await transaction(interviews.create, company.id, uuid.uuid4(), "en", 60)
        generation = found.generation_id
        await transaction(
            interview_generations.set_generated,
            generation,
            uuid.uuid4(),
            "Backend",
            75,
            {},
            str(uuid.uuid4()),
        )
        first = (await transaction(interviews.get, found.id)).question_seconds
        await transaction(
            interviews.update_settings, found.id, InterviewSettings(question_seconds=45)
        )
        await transaction(
            interview_generations.set_generated,
            generation,
            uuid.uuid4(),
            "Backend",
            75,
            {},
            str(uuid.uuid4()),
        )
        later = (await transaction(interviews.get, found.id)).question_seconds
        await transaction(
            interview_generations.set_generated,
            old.generation_id,
            uuid.uuid4(),
            "Backend",
            None,
            {},
            str(uuid.uuid4()),
        )

        return first, later, (await transaction(interviews.get, old.id)).question_seconds

    assert run(scenario()) == (75, 45, 60)
