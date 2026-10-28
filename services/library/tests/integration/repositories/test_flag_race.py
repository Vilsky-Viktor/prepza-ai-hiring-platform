import asyncio

from sqlalchemy import func, select

from library.constants.quality import QualityFlag
from library.core.db import Session
from library.models.outbox import OutboxEvent
from library.repositories import answer_stats, preparations, quality
from tests.integration.factories import interview


async def notices(question_id) -> int:
    async with Session() as session:
        return await session.scalar(
            select(func.count())
            .select_from(OutboxEvent)
            .where(OutboxEvent.data["key"].astext.contains(str(question_id)))
        )


def test_two_reviews_at_once_flag_a_question_once(run):
    """An answer and its finished topic review the question at the same moment: one flag, one
    notification, one check by the verifier."""

    async def scenario():
        results = []

        # With no statistics yet, and with statistics but no flag.
        for answered in (False, True):
            set_id = await interview(f"Race {answered}", questions=1)
            question = (await preparations.get_content(set_id)).topics[0].questions[0]

            if answered:
                await answer_stats.record_answer(
                    "race-event", question.id, question.text, ["a"], 1.0
                )

            notice = {"kind": "question_flagged", "key": f"flag:{question.id}"}
            changed = await asyncio.gather(
                *[
                    quality.change_flag(question.id, None, QualityFlag.WRONG_KEY, notice)
                    for _ in range(2)
                ]
            )
            results.append(
                (
                    sorted(changed),
                    await quality.current_flag(question.id),
                    await notices(question.id),
                )
            )

        return results

    for changed, flag, sent in run(scenario()):
        assert changed == [False, True]
        assert flag == QualityFlag.WRONG_KEY
        assert sent == 1


def test_a_flag_changed_meanwhile_is_left_as_it_is(run):
    async def scenario():
        set_id = await interview("Changed meanwhile", questions=1)
        question = (await preparations.get_content(set_id)).topics[0].questions[0]
        await quality.save_flag(question.id, QualityFlag.REWRITE)
        # Read before the rewrite flag was saved.
        changed = await quality.change_flag(question.id, None, QualityFlag.WRONG_KEY)

        return changed, await quality.current_flag(question.id)

    assert run(scenario()) == (False, QualityFlag.REWRITE)
