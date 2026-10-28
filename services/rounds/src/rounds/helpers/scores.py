from rounds.constants.rounds import CORRECT_SCORE, RoundStatus


def answer_score(right: list[int], picked: list[int]) -> int:
    """An answer's points out of CORRECT_SCORE: none with any wrong option picked, else the share
    of the right options picked (2 of 3: 67). A single-answer question scores all or nothing."""
    if not picked or any(pick not in right for pick in picked):
        return 0

    return round(CORRECT_SCORE * len(picked) / len(right))


def picked_options(answer) -> list[int]:
    """The options an answer picked: its ticks, its one pick, or none when its time ran out."""
    if answer.picks is not None:
        return list(answer.picks)

    return [] if answer.option_index is None else [answer.option_index]


def interview_finished(statuses: list[str]) -> bool:
    """True once the candidate has finished every topic session."""
    return bool(statuses) and all(status == RoundStatus.FINISHED for status in statuses)


def invite_grade(answered: int, score_sum: int, total: int, finished: bool) -> dict:
    """A candidate's share of questions answered, and their grade: percent correct of the
    answers so far, or, once they finished, of every question (unanswered ones count as wrong,
    as in each section's score)."""
    if finished:
        grade = round(score_sum / total) if total else 0
    else:
        grade = round(score_sum / answered) if answered and total else None

    return {
        "progress": round(answered / total * 100) if total else 0,
        "grade": grade,
        "finished": finished,
    }


def final_score(scores: list[int], total: int) -> int:
    """Percent correct over every question of the session; unanswered ones count as wrong."""
    return round(sum(scores) / total) if total else 0


def scored(row) -> dict:
    """The session.scored event of a finished section: its score, and for each question the
    candidate saw, whether they got it all right, the credit they earned (0 to 1: a share for a
    multi-answer one partly right) or ran out of time."""
    texts = {question["id"]: question["text"] for question in row.questions}

    return {
        "final_score": row.final_score,
        "answers": [
            {
                "question_id": str(answer.question_id),
                "question_text": texts.get(str(answer.question_id), ""),
                "correct": answer.correct,
                "credit": answer.score / CORRECT_SCORE,
                "timed_out": answer.timed_out,
            }
            for answer in row.answers
        ],
    }
