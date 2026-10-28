import uuid

from accounts.repositories import legal, user_data
from tests.integration.transactions import transaction


def test_the_terms_accepted_are_kept_once_exported_and_deleted_with_the_account(run):
    user_id = f"terms-{uuid.uuid4()}"

    async def scenario():
        await transaction(legal.accept_terms, user_id, "2026-10-10")
        # A retried sign-up keeps the first acceptance.
        await transaction(legal.accept_terms, user_id, "2026-10-10")
        exported = await transaction(user_data.export, user_id)
        await transaction(user_data.delete_user, user_id)
        # Safe to repeat: a retried deletion finds nothing left.
        await transaction(user_data.delete_user, user_id)

        return exported, await transaction(legal.accepted_terms, user_id)

    exported, left = run(scenario())

    assert [item["version"] for item in exported["terms_accepted"]] == ["2026-10-10"]
    assert left == []
