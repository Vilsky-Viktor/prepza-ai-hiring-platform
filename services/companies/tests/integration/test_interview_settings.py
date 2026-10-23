import uuid

from app.schemas.interviews import InterviewSettings
from app.storage import companies, interview_generations, interviews


def test_saving_one_setting_keeps_the_others(run):
    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        found = await interviews.create(company.id, uuid.uuid4(), "en", 60)
        await interviews.update_settings(
            found.id, InterviewSettings(question_seconds=45, pass_mark=85)
        )
        await interviews.update_settings(found.id, InterviewSettings(hired=True))

        return await interviews.get(found.id)

    saved = run(scenario())

    assert (saved.question_seconds, saved.pass_mark, saved.hired) == (45, 85, True)


def test_a_new_tests_questions_are_shared_until_the_company_keeps_them_out(run):
    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        found = await interviews.create(company.id, uuid.uuid4(), "en", 60)
        new = (await interviews.get(found.id)).keep_private
        await interviews.update_settings(found.id, InterviewSettings(keep_private=True))
        kept = await interviews.get(found.id)
        await interviews.update_settings(found.id, InterviewSettings(keep_private=False))

        return new, kept.keep_private, kept.hired, (await interviews.get(found.id)).keep_private

    # Off when made, as the terms say; on and off again leaves the other settings alone.
    assert run(scenario()) == (False, True, False, False)


def test_a_generated_test_takes_its_levels_seconds_once_and_keeps_the_companys_after(run):
    """The first completion gives the level's seconds; a later one (a retried event, a
    regeneration) keeps what the company set since; one without a level keeps the test's."""

    async def scenario():
        company = await companies.create(f"Acme {uuid.uuid4()}", "owner", "owner@example.com")
        found = await interviews.create(company.id, uuid.uuid4(), "en", 60)
        old = await interviews.create(company.id, uuid.uuid4(), "en", 60)
        generation = found.generation_id
        await interview_generations.set_generated(
            generation, uuid.uuid4(), "Backend", 75, {}, str(uuid.uuid4())
        )
        first = (await interviews.get(found.id)).question_seconds
        await interviews.update_settings(found.id, InterviewSettings(question_seconds=45))
        await interview_generations.set_generated(
            generation, uuid.uuid4(), "Backend", 75, {}, str(uuid.uuid4())
        )
        later = (await interviews.get(found.id)).question_seconds
        await interview_generations.set_generated(
            old.generation_id, uuid.uuid4(), "Backend", None, {}, str(uuid.uuid4())
        )

        return first, later, (await interviews.get(old.id)).question_seconds

    assert run(scenario()) == (75, 45, 60)
