import asyncio
import logging
import random
from collections import Counter

from prepza_common.multi_answer import is_multi

from app.helpers.prompts import checker_messages
from app.integrations import llm
from app.prompts.verify import MULTI_ANSWER_KEY, SELF_CHECK_PROMPT
from app.schemas.regenerate import RegeneratedOption
from app.schemas.verify import SelfCheck
from app.services.verify import checked_key

logger = logging.getLogger(__name__)

# Why a new question was dropped.
WRONG_KEY = "key"
OPEN_CONDITION = "condition"
NOT_CHECKED = "not checked"


async def self_check(question: dict, topic: str, level: str) -> str | None:
    """Why a new multi-answer question ({"text", "options"}) can't be kept, or None: one call
    answers it blind (no option marked, a new order) and names any condition it leaves open that
    decides an option. Its key must match and nothing may be left open. A single-answer one isn't
    checked (its keys already reach the target, evals/README.md)."""
    if not is_multi(question["options"]):
        return None

    options = [RegeneratedOption.model_validate(option) for option in question["options"]]
    order = random.sample(range(len(options)), len(options))
    prompt = SELF_CHECK_PROMPT.format(
        kind=MULTI_ANSWER_KEY,
        level=level,
        topic=topic,
        question=question["text"],
        options="\n".join(f"{number}. {options[i].answer}" for number, i in enumerate(order)),
    )

    try:
        result: SelfCheck = (
            await llm.get_verifier_llm()
            .with_structured_output(SelfCheck)
            .ainvoke(checker_messages(prompt))
        )
    except Exception:
        logger.warning("Couldn't check a new question's key; it's dropped", exc_info=True)

        return NOT_CHECKED

    if result.open_condition:
        return OPEN_CONDITION

    marked = {index for index, option in enumerate(options) if option.correct}

    return None if checked_key(options, result, order) == marked else WRONG_KEY


async def keys_that_hold(questions: list[dict], topic: str, level: str) -> list[dict]:
    """New questions ({"text", "options"}) without the multi-answer ones the self-check drops:
    each of their options must be clearly right or wrong under the conditions the question
    states. Fill-ups make up for the ones dropped."""
    reasons = await asyncio.gather(*(self_check(question, topic, level) for question in questions))
    dropped = Counter(reason for reason in reasons if reason)

    if dropped:
        logger.info("Dropped new multi-answer questions on %r: %s", topic, dict(dropped))

    return [question for question, reason in zip(questions, reasons) if reason is None]
