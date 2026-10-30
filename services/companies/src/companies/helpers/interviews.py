import math

from prepza_common.ai.multi_answer import draw

from companies.constants.interviews import DEFAULT_TOPIC_QUESTIONS, InterviewStatus
from companies.models.interviews import Interview
from companies.schemas.interviews import TopicOut


def interview_status(hired: bool, candidate_count: int) -> InterviewStatus:
    if hired:
        return InterviewStatus.HIRED

    return InterviewStatus.IN_PROCESS if candidate_count else InterviewStatus.NEW


def topic_limit(limits: dict[str, int], topic_id) -> int:
    """Questions a candidate gets from the topic: the manager's number, or the default."""
    return limits.get(str(topic_id), DEFAULT_TOPIC_QUESTIONS)


def topics_out(found: dict, limits: dict[str, int]) -> list[TopicOut]:
    return [
        TopicOut(
            id=topic["id"],
            title=topic["title"],
            subtopics=topic.get("subtopics", []),
            question_count=topic["question_count"],
            question_limit=min(topic_limit(limits, topic["id"]), topic["question_count"]),
        )
        for topic in found.get("topics", [])
    ]


def interview_questions(found: dict | None, limits: dict[str, int]) -> int | None:
    """Every question a candidate gets, over all topics. None while the interview's questions
    aren't known."""
    if not found:
        return None

    return sum(topic.question_limit for topic in topics_out(found, limits))


def interview_minutes(found: dict | None, limits: dict[str, int], seconds: int) -> int | None:
    """The whole interview's time, in minutes rounded up: every question a candidate gets at
    `seconds` each, in click and voice mode alike (a question's reading aloud counts in its
    time). None while the interview's questions aren't known."""
    questions = interview_questions(found, limits)

    if questions is None:
        return None

    return math.ceil(questions * seconds / 60)


def pick_questions(questions: list, limit: int, share: float) -> list:
    """Each candidate gets a fresh random subset with `share` of multi-answer questions
    (prepza_common.ai.multi_answer.draw), or every question when the topic has no more."""
    if limit >= len(questions):
        return questions

    return draw(questions, limit, share)


def session_topics(interview: Interview, content: dict, share: float) -> list[dict]:
    """Each topic with a fresh random subset of its questions, as rounds starts sessions. A topic
    set to 0 questions is left out: the candidate never sees it, and it never counts."""
    return [
        {
            "id": topic["id"],
            "preparation_id": content["id"],
            "title": topic["title"],
            "questions": pick_questions(
                topic["questions"], topic_limit(interview.topic_limits, topic["id"]), share
            ),
        }
        for topic in content["topics"]
        if topic_limit(interview.topic_limits, topic["id"]) > 0
    ]
