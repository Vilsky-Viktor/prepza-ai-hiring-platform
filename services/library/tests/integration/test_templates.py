import uuid

from app.constants.reuse import MIN_REUSE_ANSWERS
from app.constants.sets import Pool
from app.storage import answer_stats, preparations, quality, reuse, templates
from tests.integration.factories import COPYABLE, a_company, direction, interview


def test_templates_are_searched_and_filtered_and_keep_their_embeddings(run):
    word = uuid.uuid4().hex[:8]

    async def scenario():
        accountant = await interview(
            f"Senior accountant {word}", level="hard", template=True, embedding=direction(1)
        )
        await interview(f"Nurse {word}", level="basic", language="de", template=True)
        await interview(f"Company accountant {word}", level="hard")
        # A typed % is a percent sign, not a wildcard.
        await interview(f"100% {word}", template=True)

        def titles(rows):
            return [row.title for row in rows]

        return (
            titles(await templates.list_templates(word, None, [], 0, 10)),
            titles(await templates.list_templates(f"accountant {word}", "hard", ["en"], 0, 10)),
            titles(await templates.list_templates(word, None, ["de"], 0, 10)),
            titles(await templates.list_templates("0%", None, [], 0, 10)),
            await preparations.get_topics(accountant),
        )

    every, hard, german, percent, topics = run(scenario())

    assert sorted(every) == sorted([f"Senior accountant {word}", f"Nurse {word}", f"100% {word}"])
    assert hard == [f"Senior accountant {word}"]
    assert german == [f"Nurse {word}"]
    assert f"100% {word}" in percent
    assert len(topics) == 1


def test_templates_are_found_by_a_topic_or_a_subtopic_too(run):
    word = uuid.uuid4().hex[:8]

    async def scenario():
        await interview(
            "Platform engineer",
            topic=f"Kubernetes {word}",
            subtopics=[f"Helm charts {word}x"],
            template=True,
        )

        def titles(rows):
            return [row.title for row in rows]

        return (
            titles(await templates.list_templates(f"kubernetes {word}", None, [], 0, 10)),
            titles(await templates.list_templates(f"helm charts {word}x", None, [], 0, 10)),
        )

    by_topic, by_subtopic = run(scenario())

    assert by_topic == ["Platform engineer"]
    assert by_subtopic == ["Platform engineer"]


def test_a_template_is_copied_into_a_company_test_and_stays_a_template(run):
    async def scenario():
        template = await interview("Bookkeeper", template=True, questions=COPYABLE)
        copy = await templates.copy_template(template, a_company("9"))
        missing = await templates.copy_template(copy.id, a_company("9"))

        return (
            await preparations.get(template),
            await preparations.get(copy.id),
            await preparations.get_topics(copy.id),
            missing,
        )

    template, copy, topics, missing = run(scenario())

    assert template.kind == "template"
    assert (copy.kind, copy.owner_type, copy.owner_id) == ("interview", "company", a_company("9"))
    assert copy.title == "Bookkeeper"
    # Of the template's 40 questions, 30 went to practice: its 10 company ones were copied.
    assert [count for _, count in topics] == [10]
    # A company's test isn't a template, so it can't be copied in turn.
    assert missing is None


def test_companies_see_only_the_templates_they_can_copy(run):
    word = uuid.uuid4().hex[:8]

    async def scenario():
        # 40 questions leave 10 for companies, enough to copy; 38 leave 8, too few.
        full = await interview(f"Full {word}", template=True, questions=COPYABLE)
        short = await interview(f"Short {word}", template=True, questions=COPYABLE - 2)

        def titles(rows):
            return sorted(row.title for row in rows)

        return (
            titles(await templates.list_templates(word, None, [], 0, 10, copyable=True)),
            titles(await templates.list_templates(word, None, [], 0, 10)),
            await templates.copy_template(full, a_company("4")) is not None,
            await templates.copy_template(short, a_company("4")) is None,
        )

    copyable, every, full_copied, short_refused = run(scenario())

    assert copyable == [f"Full {word}"]
    # Practice and superadmins still list every template.
    assert every == [f"Full {word}", f"Short {word}"]
    assert full_copied and short_refused


def test_a_template_splits_its_questions_and_copies_take_only_company_ones(run):
    async def scenario():
        template = await interview("Nurse", template=True, questions=COPYABLE)
        copy = await templates.copy_template(template, a_company("3"))
        original = await preparations.get_content(template)
        copied = await preparations.get_content(copy.id)

        return original.topics[0].questions, copied.topics[0].questions

    original, copied = run(scenario())

    assert [question.pool for question in original] == ["practice"] * 30 + ["company"] * 10
    company = [question.id for question in original if question.pool == Pool.COMPANY]
    assert [question.source_question_id for question in copied] == company
    # A company interview's own questions have no pool.
    assert {question.pool for question in copied} == {None}


def test_the_bank_offers_only_proven_company_template_questions(run):
    async def scenario():
        template = await interview(
            "Bank accountant", level="hard", template=True, questions=32, embedding=direction(1)
        )
        # A company test on the same subject isn't part of the bank.
        await interview("Company accountant", level="hard", questions=3, embedding=direction(1))
        questions = (await preparations.get_content(template)).topics[0].questions
        practice, (company, unproven) = questions[0], questions[30:]

        for question in (company, practice):
            for _ in range(MIN_REUSE_ANSWERS):
                await answer_stats.record_answer(
                    str(uuid.uuid4()), question.id, question.text, ["right"], 1.0
                )

        found = await reuse.find(direction(1), "hard", "en", 10)

        return found, company.id, unproven.id, practice.id

    found, company, unproven, practice = run(scenario())
    ids = [question_id for question_id, _, _ in found]

    assert company in ids
    assert unproven not in ids and practice not in ids


def test_finished_topics_count_strong_weak_and_timeouts_for_copies_and_originals(run):
    from app.services.answer_events import handle

    async def scenario():
        template = await interview("Chemist", template=True, questions=COPYABLE)
        copy = await templates.copy_template(template, a_company("8"))
        question = (await preparations.get_content(copy.id)).topics[0].questions[0]
        result = {
            "question_id": str(question.id),
            "question_text": question.text,
            "correct": True,
            "timed_out": False,
        }
        await handle(str(uuid.uuid4()), "session.scored", {"final_score": 90, "answers": [result]})
        await handle(
            str(uuid.uuid4()),
            "session.scored",
            {"final_score": 20, "answers": [result | {"correct": False, "timed_out": True}]},
        )

        _, copy_stats, *_ = await quality.load(question.id)
        _, original_stats, *_ = await quality.load(question.source_question_id)

        return copy_stats, original_stats

    copy_stats, original_stats = run(scenario())

    for stats in (copy_stats, original_stats):
        assert (stats.strong_answers, stats.strong_correct) == (1, 1)
        assert (stats.weak_answers, stats.weak_correct) == (1, 0)
        assert stats.timeouts == 1


def test_a_new_template_never_puts_questions_reused_from_the_bank_in_practice(run):
    from prepza_common.sets import PreparationIn

    async def scenario():
        older = await interview("Older template", template=True, questions=33)
        company = (await preparations.get_content(older)).topics[0].questions[30:]
        option = [{"answer": "right", "correct": True}, {"answer": "wrong", "correct": False}]
        reused = [
            {"text": row.text, "options": option, "source_id": str(row.id)} for row in company
        ]
        fresh = [{"text": f"New question {index}?", "options": option} for index in range(31)]
        newer = await templates.create_template(
            PreparationIn.model_validate(
                {
                    "generation_id": str(uuid.uuid4()),
                    "owner_uid": "prepza",
                    "source_text": "job text",
                    "title": "Newer template",
                    "level": "medium",
                    "language": "en",
                    "requirements": [],
                    "topics": [{"title": "Python", "subtopics": [], "questions": reused + fresh}],
                }
            ),
            0.1,
        )

        return (await preparations.get_content(newer)).topics[0].questions

    rows = run(scenario())

    # Its first 30 fresh questions go to practice; the reused ones and the 31st to companies.
    assert [row.pool for row in rows] == ["company"] * 3 + ["practice"] * 30 + ["company"]
    assert all(row.source_question_id for row in rows[:3])
