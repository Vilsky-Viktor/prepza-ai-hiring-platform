import uuid

from library.constants.quality import MIN_ANSWERS, QualityFlag
from library.handlers.dispatch import handle
from library.integrations import generation
from library.repositories import preparations, quality
from tests.integration.factories import interview
from tests.integration.transactions import transaction


def test_answers_flag_a_question_once_it_has_been_shown_enough(run, monkeypatch):
    sent = []

    async def verify_question(question_id, flag):
        sent.append(flag)

    monkeypatch.setattr(generation, "verify_question", verify_question)

    async def scenario():
        template = await interview("Glazier", template=True, questions=3)
        question = (await transaction(preparations.get_content, template)).topics[0].questions[0]
        wrong = next(option["answer"] for option in question.options if not option["correct"])
        picked = {
            "question_id": str(question.id),
            "question_text": question.text,
            "option": wrong,
            "correct": False,
        }
        flags = []

        # Every candidate picks the same wrong option: the key looks wrong, once there are
        # MIN_ANSWERS answers to say so.
        for _ in range(MIN_ANSWERS):
            await handle(str(uuid.uuid4()), "answer.recorded", picked)
            _, stats, *_ = await transaction(quality.load, question.id)
            flags.append(stats.flag)

        return flags

    flags = run(scenario())

    assert flags[:-1] == [None] * (MIN_ANSWERS - 1)
    assert flags[-1] == QualityFlag.WRONG_KEY
    assert sent == [QualityFlag.WRONG_KEY]
