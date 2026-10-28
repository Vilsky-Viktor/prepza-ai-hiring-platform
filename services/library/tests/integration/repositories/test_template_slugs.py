import uuid

from alembic import command
from alembic.config import Config
from sqlalchemy import select

from library.constants.sets import Pool
from library.models.sets import QuestionSet
from library.repositories import preparations, templates
from tests.integration.factories import COPYABLE, direction, interview, question_ids, set_pool


def test_a_template_gets_a_free_slug_and_is_found_by_it(run):
    word = uuid.uuid4().hex[:8]

    async def scenario():
        first = await interview(f"Lookup {word}", template=True)
        second = await interview(f"Lookup {word}", template=True)
        company = await interview(f"Lookup {word}")

        return (
            (await templates.get_by_slug(f"lookup-{word}")).id,
            (await templates.get_by_slug(f"lookup-{word}-2")).id,
            first,
            second,
            (await preparations.get(company)).slug,
        )

    by_slug, by_second_slug, first, second, company_slug = run(scenario())

    assert (by_slug, by_second_slug) == (first, second)
    assert company_slug is None


def test_the_migration_gives_existing_templates_unique_slugs_oldest_first(run):
    word = uuid.uuid4().hex[:8]

    async def create():
        return [await interview(f"Backfill {word}", template=True) for _ in range(3)]

    async def slugs():
        from library.core.db import Session

        async with Session() as session:
            rows = await session.execute(select(QuestionSet.id, QuestionSet.slug))

            return dict(rows.all())

    ids = run(create())
    config = Config("alembic.ini")
    command.downgrade(config, "0020")
    command.upgrade(config, "head")
    found = run(slugs())

    assert [found[set_id] for set_id in ids] == [
        f"backfill-{word}",
        f"backfill-{word}-2",
        f"backfill-{word}-3",
    ]
    template_slugs = [slug for slug in found.values() if slug is not None]
    assert len(template_slugs) == len(set(template_slugs))


def test_the_sample_has_at_most_ten_practice_questions_spread_across_topics(run):
    async def scenario():
        template = await interview(
            "Sample",
            template=True,
            questions=COPYABLE,
            topic_embeddings=[direction(1), direction(0, 1)],
        )
        # An older template can be left with no practice questions after the migration.
        empty = await interview("Sample empty", template=True, questions=2)
        await set_pool(await question_ids(empty), Pool.COMPANY)

        return (
            await templates.sample_questions(template, 10),
            await templates.sample_questions(empty, 10),
        )

    sample, empty = run(scenario())

    assert len(sample) == 10
    assert all(question.pool == Pool.PRACTICE for question, _ in sample)
    assert [topic for _, topic in sample[:4]] == ["Python 0", "Python 1", "Python 0", "Python 1"]
    assert empty == []


def test_a_later_template_of_the_same_title_and_language_is_a_near_duplicate(run):
    word = uuid.uuid4().hex[:8]

    async def scenario():
        first = await interview(f"Duplicate {word}", template=True, language="de")
        same = await interview(f"DUPLICATE {word}", template=True, language="de")
        other_language = await interview(f"Duplicate {word}", template=True, language="fr")

        return (
            await templates.duplicate_ids([first, same, other_language]),
            first,
            same,
        )

    duplicates, first, same = run(scenario())

    assert first not in duplicates
    assert duplicates == {same}


def test_a_rename_moves_a_templates_updated_at(run):
    async def scenario():
        template_id = await interview(f"Rename {uuid.uuid4().hex[:8]}", template=True)
        before = (await preparations.get(template_id)).updated_at
        await preparations.set_title(template_id, "Renamed")

        return before, (await preparations.get(template_id)).updated_at

    before, after = run(scenario())

    assert after > before
