import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.constants.generation import MAX_TOPIC_NAME_LENGTH
from app.helpers.prompts import bullet_list, language_name
from app.integrations import llm
from app.models.state import State
from app.prompts.topic_revision import REVISION_REQUEST, REVISION_SYSTEM
from app.services.topic_caps import topic_caps
from app.services.topic_planning import plan_topics


async def revise_topics(state: State) -> dict:
    """Apply the reviewer's free-text instructions to the topics kept in the checkboxes."""
    caps = await topic_caps()
    messages = [
        SystemMessage(content=REVISION_SYSTEM.format(**caps, max_name=MAX_TOPIC_NAME_LENGTH)),
        HumanMessage(
            content=REVISION_REQUEST.format(
                level=state["level"],
                requirements=bullet_list(state["requirements"]),
                current=json.dumps(state["topics"], indent=2, ensure_ascii=False),
                feedback=state["feedback"],
                language=language_name(state.get("language")),
            )
        ),
    ]

    return {
        "topics": await plan_topics(messages, llm.get_generation_llm(), caps),
        "feedback": "",
        "approved": False,
    }
