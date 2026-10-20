import logging
import random
from collections import Counter
from uuid import UUID

from prepza_common.multi_answer import is_multi

from app.constants.actions import QUESTION_VERIFY
from app.constants.generation import MAX_MULTI_CORRECT
from app.constants.quality import QualityFlag
from app.helpers.prompts import bullet_list, checker_messages
from app.integrations import library, llm
from app.integrations.usage import ai_run
from app.prompts.verify import (
    CONFIRM_PROMPT,
    MULTI_ANSWER_KEY,
    SINGLE_ANSWER_KEY,
    VERIFY_PROMPT,
)
from app.schemas.regenerate import QuestionContext, RegeneratedOption, RegeneratedQuestion
from app.schemas.verify import KeyCheck, QuestionQuality
from app.services.nodes.answers import generate_answers
from app.services.regenerate import regenerate
from app.storage import key_checks

logger = logging.getLogger(__name__)


async def replace(
    question_id: UUID, context: QuestionContext, question: QuestionQuality | None = None
) -> None:
    """A new question in its place, written to avoid what users reported about it."""
    reasons = [report.reason for report in question.reports] if question else []

    if await regenerate(question_id, context, reasons) is None:
        logger.warning("Couldn't write a replacement for question %s", question_id)


def marked_answer(question: QuestionQuality) -> str:
    """The options the question marks as correct, one per line in the order shown."""
    return "\n".join(option.answer for option in question.options if option.correct)


def option_order(question: QuestionQuality) -> list[int]:
    """The marked options first, so the model doesn't take a position as a hint."""
    marked = [i for i, option in enumerate(question.options) if option.correct]

    return marked + [i for i in range(len(question.options)) if i not in marked]


def key_check_prompt(question: QuestionQuality, context: QuestionContext) -> str:
    return VERIFY_PROMPT.format(
        kind=MULTI_ANSWER_KEY if is_multi(question.options) else SINGLE_ANSWER_KEY,
        level=context.level,
        topic=context.topic,
        question=question.text,
        # Not how often each was picked: the popular answer can be the wrong one, and a few
        # people picking one together mustn't steer the check.
        options="\n".join(
            f"{number}. {question.options[i].answer}"
            for number, i in enumerate(option_order(question))
        ),
        # Reasons only, counted: a reporter's free-text comment never reaches the model, so it
        # can't steer which answer counts as correct.
        reports=bullet_list(
            [
                f"{reason}: {count}"
                for reason, count in Counter(r.reason for r in question.reports).items()
            ]
        )
        or "None",
    )


def checked_key(options: list, result: KeyCheck, order: list[int]) -> set[int] | None:
    """The options the check names as correct, as indexes into `options`; None when it named
    none, an option that isn't there, or a key of the other kind (one option for a multi-answer
    question, several for a single-answer one, or every option): the question can't keep its
    kind."""
    indexes = result.correct_indexes

    if not indexes or any(not 0 <= index < len(order) for index in indexes):
        return None

    correct = {order[index] for index in indexes}

    if (len(correct) > 1) != is_multi(options) or len(correct) > MAX_MULTI_CORRECT:
        return None

    return correct


async def blind_key(text: str, options: list, level: str, topic: str) -> set[int] | None:
    """The options a check that sees no mark, in a new order, names as correct (checked_key)."""
    order = random.sample(range(len(options)), len(options))
    prompt = CONFIRM_PROMPT.format(
        kind=MULTI_ANSWER_KEY if is_multi(options) else SINGLE_ANSWER_KEY,
        level=level,
        topic=topic,
        question=text,
        options="\n".join(f"{number}. {options[i].answer}" for number, i in enumerate(order)),
    )
    result: KeyCheck = (
        await llm.get_verifier_llm()
        .with_structured_output(KeyCheck)
        .ainvoke(checker_messages(prompt))
    )

    return checked_key(options, result, order)


async def confirmed(question: QuestionQuality, context: QuestionContext, correct: set[int]) -> bool:
    """A second, blind check names the same options `correct`."""
    found = await blind_key(question.text, question.options, context.level, context.topic)

    return found == correct


async def apply_key_check(
    question_id: UUID, question: QuestionQuality, context: QuestionContext, result: KeyCheck
) -> None:
    """Keeps the question, moves the key to the right options, or replaces a broken question. A
    key moves only when a second, blind check agrees: a moved key marks every future candidate's
    answer, so a check that doesn't hold up again replaces the question instead."""
    correct = checked_key(question.options, result, option_order(question))

    if correct is None:
        await replace(question_id, context, question)

        return

    if correct == {i for i, option in enumerate(question.options) if option.correct}:
        await library.keep_question(question_id)

        return

    if not await confirmed(question, context, correct):
        await replace(question_id, context, question)

        return

    options = [
        RegeneratedOption(answer=option.answer, correct=i in correct)
        for i, option in enumerate(question.options)
    ]
    await library.replace_question(
        question_id, RegeneratedQuestion(text=question.text, options=options)
    )


async def check_key(question_id: UUID, question: QuestionQuality, context: QuestionContext) -> None:
    """The key check right away; used when a batched check came back unusable."""
    result: KeyCheck = (
        await llm.get_verifier_llm()
        .with_structured_output(KeyCheck)
        .ainvoke(checker_messages(key_check_prompt(question, context)))
    )
    await apply_key_check(question_id, question, context, result)


async def new_options(
    question_id: UUID, question: QuestionQuality, context: QuestionContext
) -> None:
    """The same question with new options; one that turns out ambiguous is replaced."""
    result = await generate_answers(
        {
            "topic_index": 0,
            "topic": context.topic,
            "start": 0,
            "questions": [question.text],
            "level": context.level,
            "language": context.language,
            "multi": is_multi(question.options),
        }
    )
    options = result["answer_pool"][0]["options"][0]

    if not options:
        await replace(question_id, context, question)

        return

    await library.replace_question(
        question_id, RegeneratedQuestion(text=question.text, options=options)
    )


async def verify(question_id: UUID, flag: QualityFlag, now: bool = False) -> None:
    """Acts on a question the library flagged from its answers and feedback; `now` checks a
    wrong key right away (a superadmin's "Fix now"). The library's current flag wins over the
    one sent: the question may have been kept, replaced or flagged otherwise since."""
    context = await library.get_question_context(question_id)
    question = await library.get_question_quality(question_id)

    # Deleted, kept or replaced since it was flagged.
    if context is None or question is None or question.flag is None:
        return

    async with ai_run(QUESTION_VERIFY, subject_id=question_id):
        if question.flag == QualityFlag.WRONG_KEY and now:
            # Checked now, so a check still waiting in a batch is dropped: its result would
            # come after this one's.
            await key_checks.remove([question_id])
            await check_key(question_id, question, context)
        elif question.flag == QualityFlag.WRONG_KEY:
            # Nobody waits on it, so it goes in the next OpenAI batch at half price.
            await key_checks.add(question_id, question.text, marked_answer(question))
        elif question.flag == QualityFlag.WEAK_OPTIONS:
            await new_options(question_id, question, context)
        else:
            await replace(question_id, context, question)
