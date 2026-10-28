import uuid

from prepza_common.http import http

from accounts.integrations import services as account_services


def test_the_assistant_exports_and_deletes_a_users_conversations_for_accounts(run):
    """Accounts' own calls to the running assistant: signed with the assistant's key, the email
    in the body. A user who never used it has nothing to export, and deleting is safe."""
    user_id = f"accounts-{uuid.uuid4().hex[:8]}"

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
