import json

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.constants.generation import TOPIC_ATTEMPTS
from app.helpers.topics import fit_topics
from app.prompts.topic_rules import TOO_MANY_TOPICS
from app.schemas.topics import TopicList


async def plan_topics(messages: list[BaseMessage], model, caps: dict) -> list[dict]:
    """Ask for topics; when the model goes over the limit, send the list back to merge."""
    structured_llm = model.with_structured_output(TopicList)
    messages = list(messages)

    for _ in range(TOPIC_ATTEMPTS):
        result: TopicList = await structured_llm.ainvoke(messages)
        topics = [topic.model_dump() for topic in result.topics]

        if len(topics) <= caps["max_topics"]:
            break

        messages += [
            AIMessage(content=json.dumps(topics, ensure_ascii=False)),
            HumanMessage(
                content=TOO_MANY_TOPICS.format(count=len(topics), max_topics=caps["max_topics"])
            ),
        ]

    return fit_topics(topics, caps["max_subtopics"])
