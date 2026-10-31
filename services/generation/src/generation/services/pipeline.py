import uuid
from contextlib import aclosing

from langgraph.types import Command
from testee_common.ai.ai_constants import Outcome
from testee_common.limits.limits import limit

from generation.constants.actions import INTERVIEW_GENERATION, TEMPLATE_GENERATION
from generation.constants.events import GENERATION_COMPLETED
from generation.constants.generation import RECURSION_LIMIT
from generation.constants.kinds import GenerationKind
from generation.constants.statuses import Status
from generation.helpers.payload import build_preparation
from generation.helpers.progress import track_progress
from generation.helpers.questions import topic_size, topic_size_name
from generation.integrations import library
from generation.integrations.redis import get_redis
from generation.integrations.usage import ai_run
from generation.models.generation import Generation
from generation.services import outbox as outbox_service
from generation.services.run_state import is_cancelled, save
from generation.services.sample_checks import check_sample


async def run_pipeline(graph, generation: Generation, resume: dict | None) -> None:
    """Runs the graph until it pauses for review or finishes, keeping the row up to date."""
    config = {
        "configurable": {"thread_id": str(generation.id)},
        "max_concurrency": await limit(get_redis(), "GENERATION_CALLS_AT_ONCE"),
        "recursion_limit": RECURSION_LIMIT,
    }
    template = generation.kind == GenerationKind.TEMPLATE
    values = (await graph.aget_state(config)).values

    if resume is not None:
        graph_input = Command(resume=resume)
    elif values:
        # A checkpoint exists, so continue from it after a crash or a retry.
        graph_input = None
    else:
        # A change in Controls applies to generations started after it.
        values = {
            "input_text": generation.text,
            "language": generation.language,
            "template": template,
            # A company's interview reuses the shared bank's questions, never its own.
            "company_id": None if template else str(generation.company_id),
            "topic_size": await limit(get_redis(), topic_size_name(template)),
        }
        graph_input = values

    # What this run used, also when it fails: a retry or a resume records its own.
    action = TEMPLATE_GENERATION if template else INTERVIEW_GENERATION
    who = {"company_id": generation.company_id, "user_id": generation.owner_uid}

    async with ai_run(action, subject_id=generation.id, **who) as run:
        await stream_graph(graph, generation, graph_input, config, topic_size(values))

        if await is_cancelled(generation.id):
            run.outcome = Outcome.CUT


async def stream_graph(graph, generation: Generation, graph_input, config: dict, size: int) -> None:
    progress = dict(generation.progress or {})
    paused = False

    # aclosing stops the graph right away on cancel instead of leaving it to garbage collection.
    async with aclosing(graph.astream(graph_input, config, stream_mode="updates")) as stream:
        async for chunk in stream:
            # Stop spending tokens as soon as the user cancels.
            if await is_cancelled(generation.id):
                return

            # The stream ends by itself after an interrupt; leaving early would abort the run.
            if "__interrupt__" in chunk:
                topics = chunk["__interrupt__"][0].value["topics"]
                await save(generation.id, status=Status.AWAITING_REVIEW, topics=topics)
                paused = True

                continue

            if track_progress(progress, chunk, size):
                await save(generation.id, progress=progress)

    if paused or await is_cancelled(generation.id):
        return

    values = (await graph.aget_state(config)).values

    if generation.kind == GenerationKind.TEMPLATE:
        payload = build_preparation(generation.id, generation.owner_uid, generation.text, values)
        set_id = await library.create_template(payload)
        await check_sample(set_id)
        await finish(generation.id, set_id)

        return

    payload = build_preparation(generation.id, str(generation.company_id), generation.text, values)
    set_id: uuid.UUID = await library.create_interview(payload)
    # Checked before companies hears it's ready, so no candidate sees an unchecked key.
    await check_sample(set_id)
    # Companies stores the test's set and title, so its pages don't have to ask for them.
    completed = (
        GENERATION_COMPLETED,
        {
            "generation_id": str(generation.id),
            "company_id": str(generation.company_id),
            "set_id": str(set_id),
            "title": payload.title,
            # Companies gives the test its level's seconds a question.
            "level": payload.level,
        },
    )
    await finish(generation.id, set_id, completed)
    await outbox_service.flush_quietly()


async def finish(generation_id: uuid.UUID, set_id: uuid.UUID, event=None) -> None:
    """Marks the generation done with its saved set. Cancelled while the set was being saved,
    it stays cancelled, and the set nobody will use is deleted."""
    if not await save(generation_id, event, status=Status.DONE, preparation_id=set_id):
        await library.delete_set(set_id)
