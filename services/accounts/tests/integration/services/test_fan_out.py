import uuid

from prepza_common.http import http

from accounts.integrations import services as account_services


def test_the_assistant_exports_a_users_conversations_and_companies_deletes_for_accounts(run):
    """Accounts' own calls to the running assistant and companies: signed with each one's key,
    the email in the body. A user who never used them has nothing to export, and deleting in
    companies is safe to repeat."""
    user_id = f"accounts-{uuid.uuid4().hex[:8]}"

    async def scenario():
        try:
            exported = await account_services.export_user("assistant", user_id, "a@example.com")
            await account_services.delete_in_companies(user_id, "a@example.com")
            await account_services.delete_in_companies(user_id, "a@example.com")
        finally:
            await http.get_client().aclose()
            http.get_client.cache_clear()

        return exported

    assert run(scenario()) == {"assistant_conversations": [], "connected_ai_apps": []}


def test_site_exports_a_users_contact_messages_for_accounts(run):
    """Accounts' own call to the running site, signed with site's key, the email in the body:
    an address that never wrote has nothing to export."""
    user_id = f"accounts-{uuid.uuid4().hex[:8]}"
    email = f"{user_id}@example.com"

    async def scenario():
        try:
            exported = await account_services.export_user("site", user_id, email)
        finally:
            await http.get_client().aclose()
            http.get_client.cache_clear()

        return exported

    assert run(scenario()) == {"contact_messages": []}
