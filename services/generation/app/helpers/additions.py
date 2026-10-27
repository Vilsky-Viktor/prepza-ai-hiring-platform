from prepza_common.ai.sets import AdditionTopic

from app.constants.additions import ADDED_QUESTIONS_STEP


def planned(topic: AdditionTopic, count: int | None) -> tuple[int, int]:
    """The practice and company questions to write for a topic: what it lacks, for a top-up (no
    count), or a superadmin's count split a third to practice and the rest to companies."""
    if count is None:
        return topic.practice_missing, topic.company_missing

    practice = count // ADDED_QUESTIONS_STEP

    return practice, count - practice
