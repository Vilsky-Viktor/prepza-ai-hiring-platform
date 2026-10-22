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
from app.prompts.checker import MULTI_ANSWER_KEY, SINGLE_ANSWER_KEY
from app.prompts.confirm import CONFIRM_PROMPT
from app.prompts.verify import VERIFY_PROMPT
from app.schemas.regenerate import QuestionContext, RegeneratedOption, RegeneratedQuestion
from app.schemas.verify import KeyCheck, QuestionQuality
from app.services import batch_work
from app.services.regenerate import regenerate
from app.storage import key_checks

logger = logging.getLogger(__name__)


async def replace(
    question_id: UUID, context: QuestionContext, question: QuestionQuality, now: bool = False
) -> None:
    """A new question in its place, written to avoid what users reported about it: through the
    next OpenAI batch at half price, as nobody waits on it, or at once for a superadmin's "Fix
    now"."""
    reasons = [report.reason for report in question.reports]

    if not now:
        await batch_work.queue_rewrite(question_id, context, question.text, reasons)

        return

    if await regenerate(question_id, context, reasons) is None:
        logger.warning("Couldn't write a replacement for question %s", question_id)


def marked_answer(question: QuestionQuality) -> str:
    """The options the question marks as correct, one per line in the order shown."""
    return "\n".join(option.answer for option in question.options if option.correct)


def option_order(question_id: UUID | str, count: int) -> list[int]:
    """The order a key check shows the options in: shuffled, so no position hints at the marked
    key, and the same for the same question, so a batched check's reply is read in the order
    it was asked in."""
    return random.Random(str(question_id)).sample(range(count), count)


def key_check_prompt(question_id: UUID, question: QuestionQuality, context: QuestionContext) -> str:
    return VERIFY_PROMPT.format(
        kind=MULTI_ANSWER_KEY if is_multi(question.options) else SINGLE_ANSWER_KEY,
        level=context.level,
        topic=context.topic,
        question=question.text,
        # Not how often each was picked: the popular answer can be the wrong one, and a few
        # people picking one together mustn't steer the check.
        options="\n".join(
            f"{number}. {question.options[i].answer}"
            for number, i in enumerate(option_order(question_id, len(question.options)))
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


def confirm_prompt(text: str, options: list, level: str, topic: str, order: list[int]) -> str:
    """The blind confirmation's prompt: no option marked, the options in `order`."""
    return CONFIRM_PROMPT.format(
        kind=MULTI_ANSWER_KEY if is_multi(options) else SINGLE_ANSWER_KEY,
        level=level,
        topic=topic,
        question=text,
        options="\n".join(f"{number}. {options[i].answer}" for number, i in enumerate(order)),
    )


async def blind_key(text: str, options: list, level: str, topic: str) -> set[int] | None:
    """The options a check that sees no mark, in a new order, names as correct (checked_key)."""
    order = random.sample(range(len(options)), len(options))
    prompt = confirm_prompt(text, options, level, topic, order)
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
    question_id: UUID,
    question: QuestionQuality,
    context: QuestionContext,
    result: KeyCheck,
    now: bool = False,
) -> None:
    """Keeps the question, moves the key to the right options, or replaces a broken question. A
    key moves only when a second, blind check agrees: a moved key marks every future candidate's
    answer, so a check that doesn't hold up again replaces the question instead."""
    order = option_order(question_id, len(question.options))
    correct = checked_key(question.options, result, order)

    if correct is None:
        await replace(question_id, context, question, now)

        return

    if correct == {i for i, option in enumerate(question.options) if option.correct}:
        await library.keep_question(question_id)

        return

    if not await confirmed(question, context, correct):
        await replace(question_id, context, question, now)

        return

    options = [
        RegeneratedOption(answer=option.answer, correct=i in correct)
        for i, option in enumerate(question.options)
    ]
    await library.replace_question(
        question_id, RegeneratedQuestion(text=question.text, options=options)
    )


async def check_key(
    question_id: UUID, question: QuestionQuality, context: QuestionContext, now: bool = False
) -> None:
    """The key check right away: a superadmin's "Fix now" (`now`, which also replaces a broken
    question at once), or a batched check that came back unusable."""
    result: KeyCheck = (
        await llm.get_verifier_llm()
        .with_structured_output(KeyCheck)
        .ainvoke(checker_messages(key_check_prompt(question_id, question, context)))
    )
    await apply_key_check(question_id, question, context, result, now)


async def new_options(
    question_id: UUID, question: QuestionQuality, context: QuestionContext
) -> None:
    """The same question with new options, through the next OpenAI batch; one that turns out
    ambiguous is replaced."""
    reasons = [report.reason for report in question.reports]
    context = context.model_copy(update={"multi": is_multi(question.options)})
    await batch_work.queue_new_options(question_id, context, question.text, reasons)


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
            await check_key(question_id, question, context, now=True)
        elif question.flag == QualityFlag.WRONG_KEY:
            # Nobody waits on it, so it goes in the next OpenAI batch at half price.
            await key_checks.add(question_id, question.text, marked_answer(question))
        elif question.flag == QualityFlag.WEAK_OPTIONS:
            await new_options(question_id, question, context)
        else:
            await replace(question_id, context, question)
