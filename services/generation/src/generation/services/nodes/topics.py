from langchain_core.messages import HumanMessage, SystemMessage

from generation.constants.generation import MAX_TOPIC_NAME_LENGTH
from generation.helpers.prompts import bullet_list, language_name
from generation.helpers.topics import fit_topics
from generation.integrations import llm
from generation.models.state import State
from generation.prompts.topics import TOPICS_REQUEST, TOPICS_SYSTEM
from generation.repositories import draft_cache
from generation.services.topic_caps import topic_caps
from generation.services.topic_planning import plan_topics


async def generate_topics(state: State) -> dict:
    """Drafts topics; the same level and requirements reuse their earlier draft."""
    caps = await topic_caps()
    messages = [
        SystemMessage(content=TOPICS_SYSTEM.format(**caps, max_name=MAX_TOPIC_NAME_LENGTH)),
        HumanMessage(
            content=TOPICS_REQUEST.format(
                level=state["level"],
                requirements=bullet_list(state["requirements"]),
                language=language_name(state.get("language")),
            )
        ),
    ]
    prompt = "\n".join(message.content for message in messages)
    model = llm.get_generation_llm()
    topics = await draft_cache.get("topics", prompt, model)

    if topics is None:
        topics = await plan_topics(messages, model, caps)
        await draft_cache.put("topics", prompt, topics, model)

    # Drafts cached before the names had a limit are fitted too.
    return {"topics": fit_topics(topics, caps["max_subtopics"])}
