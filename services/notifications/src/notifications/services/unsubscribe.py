from notifications.constants.unsubscribe import USER_SETTINGS, UnsubscribeType
from notifications.helpers.unsubscribe import token_address
from notifications.integrations import library
from notifications.repositories import bulk_recipients, opt_outs


async def apply(payload: dict) -> None:
    """Applies a checked unsubscribe token: a user's email settings (library keeps them), or a
    candidate's wish to hear no more from a company, or about one invite's reminders."""
    kind = UnsubscribeType(payload["type"])

    if kind in USER_SETTINGS:
        await library.unsubscribe(payload["user_id"], USER_SETTINGS[kind])

        # Counted against the last campaign of that kind the user got.
        if kind in (UnsubscribeType.UPDATES, UnsubscribeType.PROMOTIONS):
            await bulk_recipients.mark_unsubscribed(payload["user_id"], kind)

        return

    invite_id = payload["invite_id"] if kind == UnsubscribeType.INVITE_REMINDERS else None
    await opt_outs.add(token_address(payload), payload["company_id"], invite_id)
