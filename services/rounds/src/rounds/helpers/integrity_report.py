"""The answer-pattern part of a candidate's report: their answers over every section as the
signals read them (helpers/answer_patterns.py), the signals that fired, and the questions to ask
about in a live interview."""

from rounds.constants.answer_patterns import DIFFICULTY_TIME, FOLLOW_UPS, PatternSignal
from rounds.constants.rounds import RoundStatus
from rounds.helpers.answer_patterns import (
    flat_timing,
    hard_half,
    pattern_counts,
    unusual_pattern,
)
from rounds.helpers.rounds import correct_indexes, find_question
from rounds.schemas.integrity import AnswerPatternsOut, FollowUp, PatternSignalOut


def expected_seconds(limit: int, difficulty: float | None) -> float:
    """What a question predicts of an honest answer's time: its own fitted time, longer the
    harder it is, when that's known."""
    if difficulty is None:
        return limit

    return limit * (1 + DIFFICULTY_TIME * (1 - difficulty))


def answer_rows(sections: list) -> list[dict]:
    """Every answer to a timed question, with its question, section and what the signals read."""
    rows = []

    for section in sections:
        for answer in section.answers:
            question = find_question(section, str(answer.question_id))

            if question is None or question.get("seconds") is None:
                continue

            difficulty = question.get("difficulty")
            rows.append(
                {
                    "question": question,
                    "topic_title": section.topic_title,
                    "topic_score": section.final_score or 0,
                    "seconds": None if answer.timed_out else answer.seconds,
                    "expected": expected_seconds(question["seconds"], difficulty),
                    "difficulty": difficulty,
                    "correct": answer.correct,
                }
            )

    return rows


def follow_ups(rows: list[dict], flagged: set[str]) -> list[FollowUp]:
    """Up to FOLLOW_UPS questions the candidate got right: first those behind a signal
    (`flagged`, their questions' ids), then from their strongest topics, the hardest first (by
    difficulty when known, else by the longest time); one a topic before a second from any."""
    right = sorted(
        (row for row in rows if row["correct"]),
        key=lambda row: (
            row["question"]["id"] not in flagged,
            -row["topic_score"],
            row["difficulty"] if row["difficulty"] is not None else 1.0,
            -row["question"]["seconds"],
        ),
    )
    topics = {row["topic_title"] for row in right}
    firsts = [next(row for row in right if row["topic_title"] == topic) for topic in topics]
    firsts.sort(key=right.index)
    chosen = (firsts + [row for row in right if row not in firsts])[:FOLLOW_UPS]

    return [follow_up(row) for row in chosen]


def follow_up(row: dict) -> FollowUp:
    question = row["question"]
    right = correct_indexes(question)
    options = [option["answer"] for option in question["options"]]

    return FollowUp(
        question_id=question["id"],
        topic_title=row["topic_title"],
        text=question["text"],
        right=[options[index] for index in right],
        wrong=next(option for index, option in enumerate(options) if index not in right),
    )


def answer_patterns(sections: list) -> AnswerPatternsOut:
    """Once every section is finished: the signals that fired over all of them, and the
    follow-up questions; nothing before. The hard questions answered right are behind an unusual
    pattern, so they come first among the follow-ups when it fired."""
    if not sections or any(s.status != RoundStatus.FINISHED for s in sections):
        return AnswerPatternsOut()

    rows = answer_rows(sections)
    signals, flagged = [], set()

    if flat_timing(rows):
        signals.append(PatternSignalOut(kind=PatternSignal.TIMING))

    if unusual_pattern(rows):
        signals.append(PatternSignalOut(kind=PatternSignal.PERSON_FIT, **pattern_counts(rows)))
        flagged = {row["question"]["id"] for row in hard_half(rows) if row["correct"]}

    return AnswerPatternsOut(signals=signals, follow_ups=follow_ups(rows, flagged))
