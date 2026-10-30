"""An interview's Discover tab: which templates' topics its practice results come from
(repositories/practice_matches.py)."""

from library.repositories import practice_matches, preparations
from tests.integration.factories import direction, interview
from tests.integration.transactions import transaction

# Directions no other test's topics point along.
SUBJECT = direction(*([0.0] * 120), 1.0)
OTHER = direction(*([0.0] * 121), 1.0)


async def topic_ids(set_id) -> list:
    return [topic.id for topic in (await transaction(preparations.get_content, set_id)).topics]


def test_only_templates_of_the_level_on_the_same_subject_match(run):
    async def scenario():
        test = await interview("Hiring", embedding=SUBJECT, level="medium")
        same = await interview("Same", embedding=SUBJECT, level="medium", template=True)
        await interview("Other subject", embedding=OTHER, level="medium", template=True)
        await interview("Other level", embedding=SUBJECT, level="hard", template=True)
        await interview("No embedding", level="medium", template=True)
        # A template's own id finds nothing: only a company's interview has a Discover tab.
        template_itself = await transaction(practice_matches.practice_topics, same)

        return (
            await transaction(practice_matches.practice_topics, test),
            await topic_ids(same),
            template_itself,
        )

    found, expected, template_itself = run(scenario())

    assert found == expected
    assert template_itself == []
