from prepza_common.events.notifications import NotificationKind, Recipient

from app.config.settings import settings
from app.helpers.member_emails import price_change_email, top_up_failed_email, top_up_paused_email
from app.integrations import companies, library
from app.services import delivery

# The bell's notifications about a company's billing that are emailed to its owners and admins
# too.
BILLING_KINDS = {
    NotificationKind.AUTO_TOP_UP_FAILED,
    NotificationKind.AUTO_TOP_UP_PAUSED,
    NotificationKind.AUTO_TOP_UP_PRICE_CHANGE,
}


def billing_email(data: dict, recipient: dict, company: str):
    """The email for one of BILLING_KINDS, to one owner or admin."""
    link = settings.site_url.rstrip("/") + data["link"]

    if data["kind"] == NotificationKind.AUTO_TOP_UP_PAUSED:
        return top_up_paused_email(recipient, company, link)

    if data["kind"] == NotificationKind.AUTO_TOP_UP_PRICE_CHANGE:
        return price_change_email(recipient, company, data["data"], link)

    return top_up_failed_email(recipient, company, settings.site_url)


async def billing_emails(data: dict, key: str) -> None:
    """An automatic top-up that failed, paused or will cost a new price, emailed at once to the
    company's owners and admins, whatever their email settings: it's about the company's
    billing. Keyed by the notification and the user, so a retried event sends nobody a second
    email."""
    if data["kind"] not in BILLING_KINDS or data["recipient"] != Recipient.COMPANY:
        return

    found = await companies.members([data["recipient_id"]])

    if not found:
        return

    [company] = found
    editors = [member["user_id"] for member in company["members"] if member["editor"]]

    for recipient in await library.recipients(editors):
        email = billing_email(data, recipient, company["name"])
        await delivery.send(email, f"events/{key}/{recipient['user_id']}")
