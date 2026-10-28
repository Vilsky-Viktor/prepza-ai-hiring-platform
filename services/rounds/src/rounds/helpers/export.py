from rounds.helpers.scores import picked_options


def answer_export(questions: list[dict], answer, practice: bool) -> dict:
    """An answer with its question and the options picked, readable without the ids.

    A timed question that ran out has no option picked; a multi-answer one can have several. Whether it was right is included only
    for practice, which is the talent's own: in a company's interview it isn't the candidate's
    to see, and across candidates it would build an answer key.
    """
    question = next((item for item in questions if item["id"] == str(answer.question_id)), None)
    picked = []

    if question:
        picked = [question["options"][index]["answer"] for index in picked_options(answer)]

    exported = {
        "question": question["text"] if question else None,
        # One option, or for a multi-answer question every one ticked; None when none.
        "your_answer": "; ".join(picked) or None,
        "at": answer.created_at,
    }

    if practice:
        exported["correct"] = answer.correct

    return exported
