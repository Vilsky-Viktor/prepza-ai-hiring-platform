import uuid

from prepza_common.http import http

from app.integrations import accounts as account_services
from app.storage import accounts, feedback, legal
from tests.integration.factories import interview, question_ids


def test_deleting_a_user_removes_their_votes_and_reports_and_the_export_has_them(run):
    async def scenario():
        set_id = await interview("Ledgers")
        first, second, _ = await question_ids(set_id)
        await feedback.rate_question(first, "gone", -1)
        await feedback.report_question(second, "gone", "unclear", "Two answers fit.")
        await feedback.rate_question(first, "stays", 1)
        exported = await accounts.export("gone")

        await accounts.delete_user("gone")
        # Safe to repeat: a retried deletion finds nothing left.
        await accounts.delete_user("gone")

        return (
            exported,
            await feedback.my_question_rating(first, "gone"),
            await feedback.has_reported(second, "gone"),
            await feedback.my_question_rating(first, "stays"),
        )

    exported, vote, reported, kept = run(scenario())

    assert exported["question_votes"] == [{"question": "Ledgers question 0?", "vote": -1}]
    [report] = exported["question_reports"]
    assert (report["question"], report["reason"]) == ("Ledgers question 1?", "unclear")
    assert (vote, reported, kept) == (None, False, 1)


def test_the_assistant_exports_and_deletes_a_users_conversations_for_library(run):
    """Library's own calls to the running assistant: signed with the assistant's key, the email
    in the body. A user who never used it has nothing to export, and deleting is safe."""
    user_id = f"library-{uuid.uuid4().hex[:8]}"

    async def scenario():
        try:
            exported = await account_services.export_user("assistant", user_id, "a@example.com")
            await account_services.delete_user("assistant", user_id, "a@example.com")
            await account_services.delete_user("assistant", user_id, "a@example.com")
        finally:
            await http.get_client().aclose()
            http.get_client.cache_clear()

        return exported

    assert run(scenario()) == {"assistant_conversations": [], "connected_ai_apps": []}


def test_the_terms_accepted_are_kept_once_exported_and_deleted_with_the_account(run):
    user_id = f"terms-{uuid.uuid4()}"

    async def scenario():
        await legal.accept_terms(user_id, "2026-10-10")
        # A retried sign-up keeps the first acceptance.
        await legal.accept_terms(user_id, "2026-10-10")
        exported = await accounts.export(user_id)
        await accounts.delete_user(user_id)

        return exported, await legal.accepted_terms(user_id)

    exported, left = run(scenario())

    assert [item["version"] for item in exported["terms_accepted"]] == ["2026-10-10"]
    assert left == []
