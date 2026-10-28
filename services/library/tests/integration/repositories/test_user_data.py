from library.repositories import feedback, user_data
from tests.integration.factories import interview, question_ids
from tests.integration.transactions import transaction


def test_deleting_a_user_removes_their_votes_and_reports_and_the_export_has_them(run):
    async def scenario():
        set_id = await interview("Ledgers")
        first, second, _ = await question_ids(set_id)
        await transaction(feedback.rate_question, first, "gone", -1)
        await transaction(feedback.report_question, second, "gone", "unclear", "Two answers fit.")
        await transaction(feedback.rate_question, first, "stays", 1)
        exported = await transaction(user_data.export, "gone")

        await transaction(user_data.delete_user, "gone")
        # Safe to repeat: a retried deletion finds nothing left.
        await transaction(user_data.delete_user, "gone")

        return (
            exported,
            await transaction(feedback.my_question_rating, first, "gone"),
            await transaction(feedback.has_reported, second, "gone"),
            await transaction(feedback.my_question_rating, first, "stays"),
        )

    exported, vote, reported, kept = run(scenario())

    assert exported["question_votes"] == [{"question": "Ledgers question 0?", "vote": -1}]
    [report] = exported["question_reports"]
    assert (report["question"], report["reason"]) == ("Ledgers question 1?", "unclear")
    assert (vote, reported, kept) == (None, False, 1)
