import asyncio

import httpx
from prepza_common.http.http import bearer

from app.config.settings import settings
from app.constants.emails import CONSENT_TEXT_VERSION, DEFAULTS
from app.main import app
from app.storage import accounts, emails
from tests.unit.test_internal import token


def test_a_user_without_a_row_has_the_defaults(run):
    assert run(emails.preferences("nobody")) == DEFAULTS


def test_each_change_is_logged_once_with_its_source_and_wording(run):
    async def scenario():
        await emails.change("ann", {"promotions": True}, "sign_in")
        # Repeated: nothing changes, so nothing more is logged.
        await emails.change("ann", {"promotions": True}, "sign_in")
        current = await emails.change("ann", {"promotions": False, "reminders": False}, "settings")

        return current, await emails.preferences("ann"), await emails.consents("ann")

    current, stored, log = run(scenario())

    assert current == stored == {**DEFAULTS, "reminders": False}
    assert [(row["setting"], row["granted"], row["source"], row["basis"]) for row in log] == [
        ("promotions", True, "sign_in", "choice"),
        ("promotions", False, "settings", "choice"),
        ("reminders", False, "settings", "choice"),
    ]
    assert {row["text_version"] for row in log} == {CONSENT_TEXT_VERSION}


def test_a_first_sign_in_without_the_opt_out_turns_updates_on_as_a_soft_opt_in(run):
    async def scenario():
        current = await emails.change("new", {"updates": True}, "sign_in")

        return current, await emails.consents("new")

    current, log = run(scenario())

    assert current == {**DEFAULTS, "updates": True}
    assert [(row["setting"], row["granted"], row["source"], row["basis"]) for row in log] == [
        ("updates", True, "sign_in", "soft_opt_in"),
    ]


def test_a_first_sign_in_with_the_opt_out_leaves_updates_off(run):
    async def scenario():
        current = await emails.change("opted-out", {"updates": False}, "sign_in")
        # Signing in again without the opt-out doesn't turn them on.
        again = await emails.change("opted-out", {"updates": True}, "sign_in")

        return current, again

    current, again = run(scenario())

    assert current["updates"] is False
    assert again["updates"] is False


def test_a_later_sign_in_never_turns_updates_back_on(run):
    async def scenario():
        await emails.change("returning", {"updates": True}, "sign_in")
        await emails.change("returning", {"updates": False}, "settings")
        current = await emails.change("returning", {"updates": True, "promotions": True}, "sign_in")

        return current, await emails.consents("returning")

    current, log = run(scenario())

    assert (current["updates"], current["promotions"]) == (False, True)
    assert [(row["setting"], row["granted"]) for row in log] == [
        ("updates", True),
        ("updates", False),
        ("promotions", True),
    ]


def test_concurrent_changes_keep_both(run):
    async def scenario():
        await asyncio.gather(
            emails.change("bob", {"updates": True}, "settings"),
            emails.change("bob", {"promotions": True}, "settings"),
        )

        return await emails.preferences("bob"), await emails.consents("bob")

    stored, log = run(scenario())

    assert (stored["updates"], stored["promotions"]) == (True, True)
    assert len(log) == 2


def test_the_export_has_them_and_deleting_the_user_removes_them(run):
    async def scenario():
        await emails.change("gone", {"promotions": True}, "sign_in")
        await emails.change("stays", {"promotions": True}, "sign_in")
        exported = await accounts.export("gone")
        await accounts.delete_user("gone")

        return (
            exported,
            await emails.preferences("gone"),
            await emails.consents("gone"),
            await emails.preferences("stays"),
        )

    exported, after, log, kept = run(scenario())

    assert exported["email_preferences"] == {**DEFAULTS, "promotions": True}
    [consent] = exported["email_consents"]
    assert (consent["setting"], consent["granted"], consent["source"]) == (
        "promotions",
        True,
        "sign_in",
    )
    assert (after, log) == (DEFAULTS, [])
    assert kept["promotions"] is True


def test_an_unsubscribe_link_turns_settings_off_once_logged_as_an_unsubscribe(run):
    async def scenario():
        await emails.change("leaving", {"updates": True}, "sign_in")
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(transport=transport, base_url="http://library") as client:
            # The same link used twice (a mail client's one-click, then the page).
            for _ in range(2):
                response = await client.post(
                    "/internal/users/leaving/unsubscribe",
                    json={"settings": ["updates", "reminders"]},
                    headers=bearer(token(settings.service_secret)),
                )

        return response.json(), await emails.consents("leaving")

    current, log = run(scenario())

    assert (current["updates"], current["reminders"]) == (False, False)
    assert [(row["setting"], row["granted"], row["source"]) for row in log] == [
        ("updates", True, "sign_in"),
        ("updates", False, "unsubscribe"),
        ("reminders", False, "unsubscribe"),
    ]


def test_several_users_preferences_are_read_at_once_with_defaults_for_the_rest(run):
    async def scenario():
        await emails.change("many-1", {"reminders": False}, "settings")

        return await emails.preferences_of(["many-1", "many-2"])

    found = run(scenario())

    assert found["many-1"] == {**DEFAULTS, "reminders": False}
    assert found["many-2"] == DEFAULTS
