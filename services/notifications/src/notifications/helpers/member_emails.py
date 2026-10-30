# The emails to prepza's users about their companies: the activity digest and reminders, which
# they may turn off, and the failed automatic top-up, a service email that always goes out.
from datetime import date

from babel.dates import format_date
from prepza_common.i18n.money import money

from notifications.constants.member_emails import COMPANIES_LINK, TOP_UP_LINK, MemberEmail
from notifications.constants.unsubscribe import UnsubscribeType
from notifications.helpers.emails import optional_email
from notifications.helpers.rendering import Section, email_language, render
from notifications.models.email import Email


def recipient_data(recipient: dict) -> dict:
    return {"email": recipient["email"], "language": recipient["language"]}


def long_date(day: str, language: str) -> str:
    """A day (YYYY-MM-DD) as the recipient's language writes it in full ("8 November 2026")."""
    return format_date(date.fromisoformat(day), "long", locale=language)


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


def price_change_email(recipient: dict, company: str, notice: dict, link: str) -> Email:
    """A service email: an automatic top-up's new price and the day it applies from, in the
    recipient's language; its button opens the company's billing page."""
    language = recipient["language"]
    data = {
        **recipient_data(recipient),
        "company": company,
        "price": money(notice["price"], notice["currency"], language),
        "new_price": money(notice["new_price"], notice["currency"], language),
        "date": long_date(notice["date"], language),
    }

    return render("top_up_price_change", data, link)


def top_up_on_email(recipient: dict, company: str, notice: dict, link: str) -> Email:
    """A service email: automatic top-up is on, with what each charge costs, the level that
    starts one, and how to turn it off; its button opens the company's billing page."""
    language = recipient["language"]
    data = {
        **recipient_data(recipient),
        "company": company,
        "price": money(notice["price"], notice["currency"], language),
        "threshold": notice["threshold"],
    }

    return render("top_up_on", data, link)


def top_up_charged_email(recipient: dict, company: str, notice: dict, link: str) -> Email:
    """A service email for one automatic charge: what was paid (tax included), the day, the
    credits it added and those available after it, and how to turn it off; its button opens the
    company's billing page. Paddle's receipt is separate."""
    language = recipient["language"]
    data = {
        **recipient_data(recipient),
        "company": company,
        "price": money(notice["price"], notice["currency"], language),
        "date": long_date(notice["date"], language),
        "credits": notice["credits"],
        "available": notice["available"],
    }

    return render("top_up_charged", data, link)


def legal_email(recipient: dict, document: str, version: str, site_url: str) -> Email:
    """A notice of a change to a legal document: a service email, whatever the settings. Its
    button opens the new version. The day it applies is written in the recipient's language."""
    kind = f"legal_{document}"
    language = email_language(kind, recipient["language"])
    data = {**recipient_data(recipient), "date": long_date(version, language)}

    return render(kind, data, f"{site_url.rstrip('/')}/{document}")
