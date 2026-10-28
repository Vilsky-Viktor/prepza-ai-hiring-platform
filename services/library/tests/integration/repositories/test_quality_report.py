import uuid

from library.repositories import answer_stats, preparations, quality, quality_report
from library.services import questions as question_service
from tests.integration.factories import interview
from tests.integration.transactions import transaction


def test_the_quality_tab_lists_flagged_and_replaced_questions(run):
    async def scenario():
        template = await interview("Quality template", template=True, questions=2)
        flagged, kept = (await transaction(preparations.get_content, template)).topics[0].questions
        await transaction(
            answer_stats.record_answer, str(uuid.uuid4()), flagged.id, flagged.text, ["right"], 1.0
        )
        await transaction(quality.save_flag, flagged.id, "wrong_key")
        await question_service.replace(
            kept.id, "A clearer question?", [{"answer": "Yes", "correct": True}]
        )
        await question_service.replace(
            kept.id, "The clearest question?", [{"answer": "Yes", "correct": True}]
        )

        return (
            await transaction(quality_report.flagged, 0, 100),
            await transaction(quality_report.replaced, None, 100),
            flagged.id,
            kept,
        )

    flagged_rows, replaced_rows, flagged_id, kept = run(scenario())

    [row] = [row for row in flagged_rows if row[0].id == flagged_id]
    _, stats, question_set, reports = row
    assert (stats.flag, stats.answers, question_set.kind, reports) == (
        "wrong_key",
        1,
        "template",
        0,
    )

    # Replaced twice: the first version shows what came next, the second the question as it is.
    first, second = sorted(
        (row for row in replaced_rows if row[0].question_id == kept.id),
        key=lambda row: row[0].replaced_at,
    )
    assert first[0].text == kept.text
    assert first[1].title == "Quality template"
    assert first[2][0] == "A clearer question?"
    assert second[0].text == "A clearer question?"
    assert second[2][0] == "The clearest question?"


def test_replaced_questions_page_by_key_after_the_last_one_shown(run):
    async def scenario():
        template = await interview("Paged template", template=True, questions=1)
        [question] = (await transaction(preparations.get_content, template)).topics[0].questions

        for text in ("Second?", "Third?", "Fourth?"):
            await question_service.replace(question.id, text, [{"answer": "Yes", "correct": True}])

        first = await transaction(quality_report.replaced, None, 2)
        rest = await transaction(quality_report.replaced, first[-1][0].id, 100)
        mine = [row[0].text for row in first + rest if row[0].question_id == question.id]

        return [row[0].id for row in first], [row[0].id for row in rest], mine

    first, rest, mine = run(scenario())

    # Newest first, no row twice.
    assert not set(first) & set(rest)
    assert mine == ["Third?", "Second?", "Paged template question 0?"]
