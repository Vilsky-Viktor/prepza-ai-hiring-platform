# The emails to prepza's users about their companies: the activity digest and reminders, which
# they may turn off, and the failed automatic top-up, a service email that always goes out.
from app.constants.member_emails import COMPANIES_LINK, TOP_UP_LINK, MemberEmail
from app.constants.unsubscribe import UnsubscribeType
from app.helpers.emails import Section, optional_email, render
from app.models.email import Email


def recipient_data(recipient: dict) -> dict:
    return {"email": recipient["email"], "language": recipient["language"]}


def digest_email(recipient: dict, sections: list[Section], site_url: str, secret: str) -> Email:
    """The day's activity in the user's companies, grouped by company; its unsubscribe link
    stops the whole digest."""
    return optional_email(
        MemberEmail.DIGEST,
        recipient_data(recipient),
        site_url.rstrip("/") + COMPANIES_LINK,
        site_url,
        secret,
        recipient["user_id"],
        UnsubscribeType.DIGEST,
        sections,
    )


def reminder_email(
    kind: MemberEmail, recipient: dict, rows: list, site_url: str, secret: str
) -> Email:
    """One kind of reminder, listing what it's about. Its button opens the top-up page for
    credits, otherwise the one interview it names, or the companies when it names several."""
    if kind == MemberEmail.LOW_CREDITS:
        link = site_url.rstrip("/") + TOP_UP_LINK
    elif len(rows) == 1:
        link = rows[0][2]
    else:
        link = site_url.rstrip("/") + COMPANIES_LINK

    return optional_email(
        kind,
        recipient_data(recipient),
        link,
        site_url,
        secret,
        recipient["user_id"],
        UnsubscribeType.REMINDERS,
        [("", rows)],
    )


def top_up_failed_email(recipient: dict, company: str, site_url: str) -> Email:
    """A service email: no unsubscribe link, as it's about the company's billing."""
    data = {**recipient_data(recipient), "company": company}

    return render("top_up_failed", data, site_url.rstrip("/") + TOP_UP_LINK)


def top_up_paused_email(recipient: dict, company: str, link: str) -> Email:
    """A service email, like the failed one; its button opens the company's billing page, where
    the card is updated."""
    data = {**recipient_data(recipient), "company": company}

    return render("top_up_paused", data, link)


def legal_email(recipient: dict, document: str, version: str, site_url: str) -> Email:
    """A notice of a change to a legal document: a service email, whatever the settings. Its
    button opens the new version."""
    data = {**recipient_data(recipient), "date": version}

    return render(f"legal_{document}", data, f"{site_url.rstrip('/')}/{document}")
