from rounds.constants.integrity import FAST_ANSWER_SECONDS, IntegritySignal
from rounds.helpers.integrity import counted_leave
from rounds.helpers.rounds import correct_indexes
from rounds.helpers.scores import picked_options
from rounds.schemas.review import AnswerView, ReviewItem


def add_signals(items: list[ReviewItem], signals: list) -> None:
    """Counts each question's page leaves (those that count) and copy attempts into its review
    item."""
    by_question = {str(item.question_id): item for item in items}

    for signal in signals:
        item = by_question.get(str(signal.question_id))

        if item is None:
            continue

        if counted_leave(signal):
            item.tab_leaves += 1
        elif signal.kind == IntegritySignal.COPY:
            item.copies += 1


def build_review(round_, reveal_all: bool = False) -> list[ReviewItem]:
    """Every question of the round in order; the right answer only for answered ones, or for
    every one with `reveal_all` (a practice round)."""
    answers = {str(answer.question_id): answer for answer in round_.answers}
    items = []

    for number, question in enumerate(round_.questions, start=1):
        answer = answers.get(question["id"])
        correct = correct_indexes(question)
        right = correct if answer or reveal_all else None
        multi = len(correct) > 1
        items.append(
            ReviewItem(
                question_id=question["id"],
                number=number,
                text=question["text"],
                options=[option["answer"] for option in question["options"]],
                multi=multi,
                correct_option_index=right[0] if right and not multi else None,
                correct_indexes=right,
                answer=(
                    AnswerView(
                        answer_id=answer.id,
                        option_index=answer.option_index,
                        picks=picked_options(answer),
                        timed_out=answer.timed_out,
                        right_picks=sum(pick in correct for pick in picked_options(answer)),
                        wrong_picks=sum(pick not in correct for pick in picked_options(answer)),
                        correct=answer.correct,
                        score=answer.score,
                        seconds=answer.seconds,
                        fast=not answer.timed_out
                        and answer.seconds is not None
                        and answer.seconds < FAST_ANSWER_SECONDS,
                    )
                    if answer
                    else None
                ),
            )
        )

    return items
