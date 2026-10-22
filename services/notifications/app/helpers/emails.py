from html import escape

from app.constants.unsubscribe import SETTINGS_PATH, UnsubscribeType
from app.constants.webhooks import (
    CANDIDATE_INVITE_KIND,
    CANDIDATE_REMINDER_KIND,
    COMPANY_TAG,
    ID_TAG,
    KIND_TAG,
)
from app.helpers.attachments import pdf_name
from app.helpers.rendering import Section, email_language, render
from app.helpers.unsubscribe import candidate_token, one_click_headers, page_url, user_token
from app.models.email import Email
from app.templates.contact import CONTACT_HTML, CONTACT_SUBJECT, CONTACT_TEXT
from app.templates.emails import EMAILS


def invite_tags(kind: str, invite_id: str | None) -> dict[str, str]:
    """Events saved before invites carried their id get no tags."""
    if invite_id is None:
        return {}

    return {KIND_TAG: kind, ID_TAG: invite_id}


def with_logo(data: dict, site_url: str) -> dict:
    """The invite's data with the company logo's full address, when the company has a logo."""
    path = data.get("logo_path")

    return {**data, "logo_url": f"{site_url.rstrip('/')}{path}"} if path else data


def candidate_invite_email(data: dict, site_url: str, secret: str) -> Email:
    """The invite, with a link that stops the company's emails to this address (events saved
    before invites carried the company's id have none)."""
    data = with_logo(data, site_url)
    links = (
        [
            (
                "stop_company",
                page_url(site_url, candidate_token(data, UnsubscribeType.COMPANY, secret)),
            )
        ]
        if data.get("company_id")
        else []
    )
    email = render("candidate", data, f"{site_url.rstrip('/')}/invite/{data['token']}", links)
    email.tags = invite_tags(CANDIDATE_INVITE_KIND, data.get("invite_id"))
    email.candidate = True

    return email


def candidate_joined_email(data: dict, site_url: str, secret: str) -> Email:
    """For someone who started through a test's shareable link: their own invite link, to
    continue if they leave. Untagged: a bounce leaves the invite as it is, as they're already
    taking the test."""
    data = with_logo(data, site_url)
    company = candidate_token(data, UnsubscribeType.COMPANY, secret)

    email = render(
        "joined",
        data,
        f"{site_url.rstrip('/')}/invite/{data['token']}",
        [("stop_company", page_url(site_url, company))],
    )
    email.candidate = True

    return email


def candidate_reminder_email(data: dict, site_url: str, secret: str) -> Email:
    """The one reminder to a candidate who hasn't started: the same invite link. Tagged with the
    invite and the company, so a bounce marks the invite undelivered and a spam complaint stops
    this invite's reminders. Its links stop those reminders or all the company's emails; a mail
    client's own unsubscribe stops the reminders."""
    data = with_logo(data, site_url)
    links = []
    headers = {}

    if data.get("company_id") and data.get("invite_id"):
        reminders = candidate_token(data, UnsubscribeType.INVITE_REMINDERS, secret)
        company = candidate_token(data, UnsubscribeType.COMPANY, secret)
        links = [
            ("stop_reminders", page_url(site_url, reminders)),
            ("stop_company", page_url(site_url, company)),
        ]
        headers = one_click_headers(site_url, reminders)

    email = render("reminder", data, f"{site_url.rstrip('/')}/invite/{data['token']}", links)
    email.tags = invite_tags(CANDIDATE_REMINDER_KIND, data.get("invite_id"))
    email.candidate = True

    if email.tags and data.get("company_id"):
        email.tags[COMPANY_TAG] = data["company_id"]
    email.headers.update(headers)

    return email


def member_invite_email(data: dict, site_url: str) -> Email:
    """The owner's invite to join the company's team, as an admin or a viewer (the role's name in
    the email's language), with the join link."""
    data = with_logo(data, site_url)
    roles = EMAILS[email_language("member", data.get("language"))]["member"]["roles"]
    link = f"{site_url.rstrip('/')}/join/{data['token']}"

    return render("member", {**data, "role": roles[data["role"]]}, link)


def optional_email(
    kind: str,
    data: dict,
    link: str,
    site_url: str,
    secret: str,
    user_id: str,
    unsubscribe: UnsubscribeType,
    sections: list[Section] = (),
    markdown: str = "",
) -> Email:
    """An email a prepza user may turn off (the activity digest, reminders, updates, offers):
    the `kind` email, with "Unsubscribe" (from `unsubscribe`) and "Change your email settings"
    under its footer, and the one-click unsubscribe headers mail clients show as a button. Sent
    from the optional emails' own address, and tagged with the user and `unsubscribe`, so a spam
    complaint about it turns it off (services/webhooks.py)."""
    token = user_token(user_id, unsubscribe, secret)
    links = [
        ("unsubscribe", page_url(site_url, token)),
        ("email_settings", site_url.rstrip("/") + SETTINGS_PATH),
    ]
    email = render(kind, data, link, links, sections, markdown)
    email.headers.update(one_click_headers(site_url, token))
    email.optional = True
    email.tags = {KIND_TAG: unsubscribe, ID_TAG: user_id}

    return email


def report_email(data: dict, site_url: str) -> Email:
    """A PDF report, from a company member to someone such as a hiring manager: a candidate's,
    or all of a test's candidates' ("kind": "candidates"); replying answers the member."""
    kind = data.get("kind", "report")
    texts = {key: value for key, value in data.items() if key not in ("pdf", "kind")}
    email = render(kind, texts, site_url)
    email.reply_to = data["reply_to"]
    # Named in the email's language: its heading, then the candidate or the test.
    heading = EMAILS[email_language(kind, data.get("language"))][kind]["heading"]
    named = data.get("title") if kind == "candidates" else data.get("candidate")
    email.attachments = [(pdf_name(heading, named or ""), data["pdf"])]

    return email


def contact_email(data: dict, inbox: str) -> Email:
    """The contact page's message, to prepza's inbox; replying answers the visitor."""
    safe = {key: escape(str(value)) for key, value in data.items()}

    return Email(
        to=inbox,
        # One line, whatever the visitor typed as their name.
        subject=CONTACT_SUBJECT.format(name=" ".join(data["name"].split())),
        html=CONTACT_HTML.format(**safe),
        text=CONTACT_TEXT.format(**data),
        reply_to=data["email"],
    )
