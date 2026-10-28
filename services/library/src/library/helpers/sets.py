import uuid

from prepza_common.ai.sets import PreparationIn

from library.constants.reuse import MIN_COPY_QUESTIONS
from library.constants.sets import PLATFORM_OWNER, OwnerType, Pool, SetKind
from library.helpers.pools import assign_pools
from library.models.sets import Question, QuestionSet, Topic


def new_topics(preparation: PreparationIn) -> list[Topic]:
    """The topics and questions of a generated set, ready to save."""
    return [
        Topic(
            position=ti,
            title=topic.title,
            subtopics=topic.subtopics,
            questions=[
                Question(
                    position=qi,
                    text=question.text,
                    options=[option.model_dump() for option in question.options],
                    source_question_id=question.source_id,
                )
                for qi, question in enumerate(topic.questions)
            ],
        )
        for ti, topic in enumerate(preparation.topics)
    ]


def new_set(payload: PreparationIn, kind: SetKind, owner_type: OwnerType, owner_id: str):
    return QuestionSet(
        generation_id=payload.generation_id,
        kind=kind,
        owner_type=owner_type,
        owner_id=owner_id,
        title=payload.title,
        source_text=payload.source_text,
        level=payload.level,
        language=payload.language,
        requirements=payload.requirements,
        topics=new_topics(payload),
        topic_count=len(payload.topics),
    )


def new_interview(payload: PreparationIn) -> QuestionSet:
    """A company's interview: always private."""
    return new_set(payload, SetKind.INTERVIEW, OwnerType.COMPANY, payload.owner_uid)


def new_template(payload: PreparationIn, share: float) -> QuestionSet:
    """An admin's template; `share` of each topic's practice questions are multi-answer
    (assign_pools)."""
    template = new_set(payload, SetKind.TEMPLATE, OwnerType.PLATFORM, PLATFORM_OWNER)

    for topic in template.topics:
        assign_pools(topic.questions, share)

    return template


def copied(template: QuestionSet, company_id: str) -> tuple[QuestionSet, list[uuid.UUID]] | None:
    """A company's own test made from a template (its topics and questions loaded), with no
    generation: its topics with their company questions, each question remembering its original
    so its answers count there too, and the template topics they came from (for their
    embeddings). Topics with fewer than MIN_COPY_QUESTIONS company questions are skipped. None
    when none of its topics is left."""
    kept = []

    for topic in template.topics:
        company = [q for q in topic.questions if q.pool == Pool.COMPANY]

        if len(company) >= MIN_COPY_QUESTIONS:
            kept.append((topic, company))

    if not kept:
        return None

    copy = QuestionSet(
        kind=SetKind.INTERVIEW,
        owner_type=OwnerType.COMPANY,
        owner_id=company_id,
        title=template.title,
        source_text=template.source_text,
        level=template.level,
        language=template.language,
        requirements=template.requirements,
        topic_count=len(kept),
        topics=[
            Topic(
                position=position,
                title=topic.title,
                subtopics=topic.subtopics,
                questions=[
                    Question(
                        position=q.position,
                        text=q.text,
                        options=q.options,
                        source_question_id=q.id,
                    )
                    for q in company
                ],
            )
            for position, (topic, company) in enumerate(kept)
        ],
    )

    return copy, [topic.id for topic, _ in kept]
