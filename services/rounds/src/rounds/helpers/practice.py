from itertools import groupby

from testee_common.ai.multi_answer import draw

from rounds.constants.practice import PRACTICE_TIMINGS, PRACTICE_TOPIC_QUESTIONS
from rounds.constants.rounds import RoundStatus
from rounds.helpers.review import build_review
from rounds.helpers.scores import final_score, interview_finished
from rounds.schemas.library import TopicQuestions
from rounds.schemas.practice import (
    PracticeRoundOut,
    PracticeRoundSummary,
    PracticeStatusOut,
    PracticeTimingOut,
    PracticeTopicProgress,
    PracticeTopicResult,
)


def practice_topics(content: dict, share: float) -> list[TopicQuestions]:
    """A round's questions: up to PRACTICE_TOPIC_QUESTIONS from each topic, fresh at random, with
    `share` of multi-answer ones (testee_common.ai.multi_answer.draw)."""
    return [
        TopicQuestions(
            id=topic["id"],
            preparation_id=content["id"],
            title=topic["title"],
            questions=draw(topic["questions"], PRACTICE_TOPIC_QUESTIONS, share),
        )
        for topic in content["topics"]
    ]


def topic_sizes(content: dict) -> dict[str, int]:
    """How many questions a round on the template asks on each topic, by the topic's id: up to
    PRACTICE_TOPIC_QUESTIONS."""
    return {
        str(topic["id"]): min(PRACTICE_TOPIC_QUESTIONS, len(topic["questions"]))
        for topic in content["topics"]
    }


def timing_seconds(base: int, timing: str) -> int | None:
    """The seconds each question has with `timing`, from the level's `base`; None is untimed."""
    factor = PRACTICE_TIMINGS[timing]

    return None if factor is None else base * factor


def practice_timings(base: int) -> list[PracticeTimingOut]:
    """Every time per question a talent can choose, from the level's `base` seconds."""
    return [
        PracticeTimingOut(id=timing, seconds=timing_seconds(base, timing))
        for timing in PRACTICE_TIMINGS
    ]


def round_grade(rows: list) -> tuple[bool, int | None]:
    """Whether every section of the round is finished, and then its grade over every question
    (unanswered ones count as wrong)."""
    finished = interview_finished([row.status for row in rows])
    scores = [answer.score for row in rows for answer in row.answers]
    total = sum(len(row.questions) for row in rows)

    return finished, final_score(scores, total) if finished else None


def round_out(rows: list, title: str | None, language: str | None = None) -> PracticeRoundOut:
    """A round's results; the questions and right answers only once it's finished."""
    finished, grade = round_grade(rows)
    open_row = next((row for row in rows if row.status != RoundStatus.FINISHED), None)

    return PracticeRoundOut(
        round_id=rows[0].candidate_invite_id,
        template_id=rows[0].interview_set_id,
        title=title,
        language=language,
        finished=finished,
        grade=grade,
        answered=sum(1 for row in rows for answer in row.answers if not answer.timed_out),
        total=sum(len(row.questions) for row in rows),
        started_at=rows[0].started_at,
        open_session_id=open_row.id if open_row else None,
        topics=[
            PracticeTopicResult(
                session_id=row.id,
                title=row.topic_title,
                score=row.final_score,
                review=build_review(row, reveal_all=True) if finished else [],
            )
            for row in rows
        ],
    )


def round_summaries(rows: list) -> list[PracticeRoundSummary]:
    """A talent's rounds on one template, newest first, from all their sessions on it."""
    rows = sorted(rows, key=lambda row: (row.candidate_invite_id, row.started_at))
    rounds = []

    for round_id, sections in groupby(rows, key=lambda row: row.candidate_invite_id):
        sections = list(sections)
        finished, grade = round_grade(sections)
        answered = sum(len(row.answers) for row in sections)
        total = sum(len(row.questions) for row in sections)
        rounds.append(
            PracticeRoundSummary(
                round_id=round_id,
                started_at=sections[0].started_at,
                finished=finished,
                progress=round(answered / total * 100) if total else 0,
                grade=grade,
            )
        )

    return sorted(rounds, key=lambda item: item.started_at, reverse=True)


def topic_progress(rows: list) -> list[PracticeTopicProgress]:
    """Each topic's answered questions out of its total in the talent's latest round, finished
    or not."""
    if not rows:
        return []

    latest = max(rows, key=lambda row: row.started_at).candidate_invite_id

    return [
        PracticeTopicProgress(
            topic_id=row.topic_id, answered=len(row.answers), total=len(row.questions)
        )
        for row in rows
        if row.candidate_invite_id == latest
    ]


def practice_statuses(rows: list) -> list[PracticeStatusOut]:
    """Each practiced template's status from its latest round's sections, by the same count as
    the practice page's topics (topic_progress): completed once every topic's questions are all
    answered, in progress once any is answered, with the topics answered to the end; a round
    without an answer is left out, as never started. A round that ended, or a topic that
    finished, with questions left unanswered isn't completed."""
    topics = {}

    for row in rows:
        topics.setdefault(row.interview_set_id, []).append((len(row.answers), len(row.questions)))

    return [
        PracticeStatusOut(
            template_id=template_id,
            status="completed" if all(a >= total for a, total in found) else "in_progress",
            topics_done=sum(1 for a, total in found if a >= total),
            topics_total=len(found),
        )
        for template_id, found in topics.items()
        if any(a for a, _ in found)
    ]
