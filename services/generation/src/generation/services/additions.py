import asyncio
import logging
import math

from prepza_common.ai.examples import example_count, example_range, is_formal, pick, pool_share
from prepza_common.ai.multi_answer import multi_count, multi_share
from prepza_common.ai.sets import (
    AddedQuestionsIn,
    AdditionContext,
    AdditionTopic,
    QuestionIn,
    TopicAdditionIn,
)
from prepza_common.limits.limits import limit

from generation.constants.actions import TEMPLATE_GENERATION
from generation.constants.generation import QUESTION_OVERSAMPLE
from generation.constants.reuse import MAX_REUSE_SHARE
from generation.constants.statuses import Status
from generation.helpers.additions import planned
from generation.helpers.questions import (
    count_examples,
    count_multi,
    merge_buckets,
    normalize,
    question_calls,
    shifted,
    split_count,
)
from generation.integrations import library
from generation.integrations.redis import get_redis
from generation.integrations.usage import ai_run, embed
from generation.models.generation import Generation
from generation.repositories import generations
from generation.schemas.library import ReuseIn
from generation.services.dedupe import distinct_by_meaning
from generation.services.nodes.questions import focus_for, generate_questions
from generation.services.nodes.reuse import topic_text
from generation.services.sample_checks import check_topics
from generation.services.top_up import TopicShortError, top_up

logger = logging.getLogger(__name__)


class TemplateGoneError(Exception):
    """The template was deleted before its questions were added."""


async def run_addition(generation: Generation) -> None:
    """Adds questions to every topic of a template (preparation_id): what each lacks for a
    top-up, or a superadmin's count. Written as a new template's are, then saved all at once,
    so a failure leaves the template as it was; interviews already copied from it don't change.
    """
    context = await library.get_addition_context(generation.preparation_id)

    if context is None:
        raise TemplateGoneError(str(generation.preparation_id))

    plans = [planned(topic, generation.question_count) for topic in context.topics]

    # What this run used, also when it fails, as a generation's run records it.
    async with ai_run(TEMPLATE_GENERATION, user_id=generation.owner_uid, subject_id=generation.id):
        written = await write(generation, context, plans)

    ids = await library.add_questions(generation.preparation_id, AddedQuestionsIn(topics=written))
    await check_topics(ids)
    await generations.update(generation.id, status=Status.DONE)


async def write(
    generation: Generation, context: AdditionContext, plans: list[tuple[int, int]]
) -> list[TopicAdditionIn]:
    """Each topic's new questions; topics with nothing to add are left out. Bank questions go
    to the company side only, at most half of it; the practice side is always freshly written."""
    # A bank question goes into one topic at most, and never repeats one the template has.
    taken = {normalize(text) for topic in context.topics for text in topic.texts}
    work = []

    for topic, (practice, company) in zip(context.topics, plans):
        if practice + company == 0:
            continue

        reused = await bank_questions(topic, math.floor(company * MAX_REUSE_SHARE), context, taken)
        work.append((topic, practice, company, reused))

    calls = [len(tasks_for(topic, p + c - len(r), 0, [], context)) for topic, p, c, r in work]
    progress = {"done": 0, "total": sum(calls), "topics": len(work), "topics_ready": 0}
    calls_at_once = asyncio.Semaphore(await limit(get_redis(), "GENERATION_CALLS_AT_ONCE"))
    share = await multi_share(get_redis())

    async def step(topic_done: bool = False) -> None:
        if topic_done:
            progress["topics_ready"] += 1
        else:
            progress["done"] = min(progress["done"] + 1, progress["total"])

        await generations.update(generation.id, progress=dict(progress))

    await generations.update(generation.id, progress=dict(progress))

    async def topic_questions(topic, practice, company, reused) -> TopicAdditionIn:
        # Each side holds its share of multi-answer questions and, on material in a formal
        # notation, of questions with an example; bank ones count toward the company side's.
        bank = [question.model_dump() for question in reused]
        company_multi = max(multi_count(company, share) - count_multi(bank), 0)
        company_multi = min(company_multi, company - len(reused))
        formal = is_formal(topic.texts)
        low, high = example_range(practice, formal)
        company_low, company_high = shifted(example_range(company, formal), count_examples(bank))
        fresh = await fresh_questions(
            topic,
            practice + company - len(reused),
            multi_count(practice, share) + company_multi,
            (low + company_low, high + company_high),
            reused,
            context,
            calls_at_once,
            step,
        )
        await step(topic_done=True)
        practice_side, company_side = pool_share(fresh + bank, fresh, practice, share)

        return TopicAdditionIn(
            topic_id=topic.id,
            practice=[QuestionIn.model_validate(question) for question in practice_side],
            company=reused + [QuestionIn.model_validate(question) for question in company_side],
        )

    return list(await asyncio.gather(*(topic_questions(*item) for item in work)))


async def bank_questions(
    topic: AdditionTopic, count: int, context: AdditionContext, taken: set[str]
) -> list[QuestionIn]:
    """Up to `count` proven company questions from the bank on a similar topic. Reuse only
    saves cost, so any failure means writing them all instead."""
    if count <= 0:
        return []

    try:
        [embedding] = await embed(
            [topic_text({"main_topic": topic.title, "subtopics": topic.subtopics})]
        )
        found = await library.find_reusable(
            ReuseIn(
                embedding=embedding, level=context.level, language=context.language, count=count
            )
        )
    except Exception:
        logger.exception("Couldn't find questions to reuse for topic %s", topic.id)

        return []

    found = [question for question in found if normalize(question.text) not in taken]
    taken.update(normalize(question.text) for question in found)

    return found


def tasks_for(
    topic: AdditionTopic, count: int, multi: int, existing: list[str], context: AdditionContext
):
    """The question calls that write `count` questions for a topic, `multi` of them
    multi-answer and, on material in a formal notation, a third with an example, spread as a new
    template's: each subtopic gets its share, split into calls that take turns at the angles."""
    if count <= 0:
        return []

    subtopics = topic.subtopics or [topic.title]
    calls = question_calls(len(subtopics), count)
    per_subtopic = math.ceil(count * QUESTION_OVERSAMPLE / len(subtopics))
    sizes = [size for _ in subtopics for size in split_count(per_subtopic, calls)]
    multis = split_count(multi, len(sizes))
    shown = split_count(example_count(count), len(sizes))
    tasks = []

    for subtopic in subtopics:
        for call in range(calls):
            size = sizes[len(tasks)]
            tasks.append(
                {
                    "topic_index": 0,
                    "topic": topic.title,
                    "subtopic_index": len(tasks),
                    "subtopic": subtopic,
                    "count": size,
                    "multi": min(multis[len(tasks)], size),
                    "examples": min(shown[len(tasks)], size),
                    "level": context.level,
                    "existing": existing,
                    "focus": focus_for(call, calls),
                    "language": context.language,
                }
            )

    return tasks


async def fresh_questions(
    topic: AdditionTopic,
    count: int,
    multi: int,
    examples: tuple[int, int],
    reused: list[QuestionIn],
    context: AdditionContext,
    limit: asyncio.Semaphore,
    step,
) -> list[dict]:
    """`count` new questions with their options, `multi` of them multi-answer and from
    examples[0] to examples[1] with an example, different from every one the topic has and the
    reused ones, in words and in meaning; topped up as a new template's topics are (top_up)."""
    existing = topic.texts + [question.text for question in reused]

    async def call(task: dict) -> list[dict]:
        async with limit:
            result = await generate_questions(task)

        await step()

        return result["question_pool"][0]["questions"]

    buckets = await asyncio.gather(
        *(call(task) for task in tasks_for(topic, count, multi, existing, context))
    )
    taken = {normalize(text) for text in existing}
    merged = [
        question for question in merge_buckets(buckets) if normalize(question["text"]) not in taken
    ]
    kept = await distinct_by_meaning(
        existing + [question["text"] for question in merged], keep_first=len(existing)
    )
    distinct = [merged[index - len(existing)] for index in kept if index >= len(existing)]
    questions = pick(distinct, count, multi, examples)[0]
    item = {
        "topic": topic.title,
        "subtopics": topic.subtopics,
        "questions": existing + [question["text"] for question in questions],
    }
    state = {"level": context.level, "language": context.language}
    await top_up(item, questions, count, multi, examples, state)

    if len(questions) < count:
        raise TopicShortError(f"Topic {topic.title!r} has only {len(questions)} new questions")

    return questions
