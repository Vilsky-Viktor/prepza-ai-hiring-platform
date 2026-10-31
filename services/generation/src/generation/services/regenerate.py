import asyncio
import logging
from uuid import UUID

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from testee_common.ai.examples import has_example

from generation.constants.generation import REGENERATE_ATTEMPTS, REGENERATE_TIMEOUT_SECONDS
from generation.helpers.prompts import bullet_list, language_name
from generation.helpers.questions import normalize, readable, with_example
from generation.integrations import library, llm, usage
from generation.prompts.regenerate import (
    MULTI_ANSWER_KIND,
    REGENERATE_REQUEST,
    REGENERATE_SYSTEM,
    REPORT_GUIDANCE,
    REPORTS,
    SINGLE_ANSWER_KIND,
    WITH_EXAMPLE,
    WITHOUT_EXAMPLE,
)
from generation.schemas.questions import NewQuestion
from generation.schemas.regenerate import QuestionContext, RegeneratedOut, RegeneratedQuestion
from generation.services.answers import generate_answers
from generation.services.dedupe import distinct_by_meaning

logger = logging.getLogger(__name__)


def reported(reasons: list[str]) -> str:
    """What users reported about the replaced question, as the prompt tells it (REPORTS), or
    nothing when no reason has guidance."""
    guidance = [
        REPORT_GUIDANCE[reason] for reason in dict.fromkeys(reasons) if reason in REPORT_GUIDANCE
    ]

    return REPORTS.format(reports=bullet_list(guidance)) + "\n" if guidance else ""


def question_messages(
    context: QuestionContext, reasons: list[str], existing: list[str]
) -> list[BaseMessage]:
    """The call for a new question of the replaced one's kind, unlike every one in `existing`."""
    request = REGENERATE_REQUEST.format(
        kind=MULTI_ANSWER_KIND if context.multi else SINGLE_ANSWER_KIND,
        example=WITH_EXAMPLE if context.example else WITHOUT_EXAMPLE,
        reports=reported(reasons),
        level=context.level,
        topic=context.topic,
        subtopics=", ".join(context.subtopics) or context.topic,
        existing=bullet_list(existing),
        language=language_name(context.language),
    )

    return [SystemMessage(content=REGENERATE_SYSTEM), HumanMessage(content=request)]


async def accepted(context: QuestionContext, result: NewQuestion, taken: set[str]) -> str:
    """The new question's text when it can replace the old one (readable, an example exactly
    when the old one had one, unlike every question in the topic in words and in meaning);
    otherwise an empty string."""
    text = with_example(result.question, result.example, result.example_language)

    if (
        text
        and readable(result.question, result.example)
        and has_example(text) == context.example
        and normalize(text) not in taken
    ):
        texts = [*context.existing, text]
        kept = await distinct_by_meaning(texts, keep_first=len(context.existing))

        if len(kept) == len(texts):
            return text

    return ""


async def new_question(context: QuestionContext, reasons: list[str]) -> str | None:
    """A question of the replaced one's kind, with an example when it had one, that neither
    repeats nor rephrases any existing one in the topic; written to avoid what users reported
    (`reasons`)."""
    structured_llm = llm.get_generation_llm().with_structured_output(NewQuestion)
    existing = list(context.existing)
    taken = {normalize(text) for text in existing}

    for _ in range(REGENERATE_ATTEMPTS):
        result: NewQuestion = await structured_llm.ainvoke(
            question_messages(context, reasons, existing)
        )
        text = await accepted(context, result, taken)

        if text:
            return text

        existing.append(with_example(result.question, result.example, result.example_language))

    return None


async def write(context: QuestionContext, reasons: list[str]) -> tuple[str, list] | None:
    """A new question of the same kind as the one it replaces (context.multi), with its options,
    or None when no unambiguous one came out."""
    for _ in range(REGENERATE_ATTEMPTS):
        text = await new_question(context, reasons)

        if text is None:
            return None

        result = await generate_answers(
            {
                "topic_index": 0,
                "topic": context.topic,
                "start": 0,
                "questions": [text],
                "level": context.level,
                "language": context.language,
                "multi": context.multi,
            }
        )
        options = result["answer_pool"][0]["options"][0]

        if options:
            return text, options

        # No options means the question was ambiguous; never offer it again.
        context = context.model_copy(update={"existing": [*context.existing, text]})

    return None


async def regenerate(
    question_id: UUID, context: QuestionContext, reasons: list[str] | None = None
) -> RegeneratedOut | None:
    """Writes a new question with its options and saves it in place of the old one, avoiding
    what users reported about it (`reasons`, report reasons). Writing has
    REGENERATE_TIMEOUT_SECONDS; past it the old question stays, as the caller has given up."""
    try:
        async with asyncio.timeout(REGENERATE_TIMEOUT_SECONDS):
            written = await write(context, reasons or [])
    except TimeoutError:
        logger.warning("Regenerating question %s ran out of time; it stays as it was", question_id)
        usage.cut()

        return None

    if written is None:
        return None

    text, options = written
    await library.replace_question(question_id, RegeneratedQuestion(text=text, options=options))

    return RegeneratedOut(id=question_id, text=text)
