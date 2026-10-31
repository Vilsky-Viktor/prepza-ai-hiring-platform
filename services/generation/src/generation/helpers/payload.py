from uuid import UUID

from testee_common.ai.sets import PreparationIn, QuestionIn, TopicIn
from testee_common.config.constants import DEFAULT_LANGUAGE

from generation.helpers.questions import topic_size


def build_preparation(
    generation_id: UUID, owner_uid: str, source_text: str, values: dict
) -> PreparationIn:
    """Turn the final graph state into the library payload.

    Questions without options are skipped; the spare ones after them fill the topic up to its count.
    """
    topics = []
    embeddings = values.get("topic_embeddings") or []

    for index, item in enumerate(values["final"]):
        # Bank questions come first; fill-ups added later, and runs saved before the bank, have
        # no source id.
        sources = item.get("source_ids") or []
        sources = sources + [None] * (len(item["questions"]) - len(sources))
        questions = [
            QuestionIn(text=text, options=options, source_id=source)
            for text, options, source in zip(item["questions"], item["answer_options"], sources)
            if options
        ]
        topics.append(
            TopicIn(
                title=item["topic"],
                subtopics=item["subtopics"],
                questions=questions[: topic_size(values)],
                embedding=embeddings[index] if embeddings else None,
            )
        )

    return PreparationIn(
        generation_id=generation_id,
        owner_uid=owner_uid,
        source_text=source_text,
        title=values["title"],
        level=values["level"],
        requirements=values["requirements"],
        topics=topics,
        language=values.get("language") or DEFAULT_LANGUAGE,
    )
