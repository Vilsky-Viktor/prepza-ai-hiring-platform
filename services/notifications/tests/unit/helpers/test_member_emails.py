import string
from datetime import datetime
from types import SimpleNamespace

import pytest
from testee_common.config.constants import DEFAULT_LANGUAGE, LANGUAGES
from testee_common.i18n.plurals import PLURAL

from notifications.constants.email import AUTOMATED_HEADERS
from notifications.constants.member_emails import MemberEmail
from notifications.helpers.member_emails import (
    digest_email,
    price_change_email,
    reminder_email,
    top_up_failed_email,
    top_up_paused_email,
)
from notifications.helpers.member_selection import (
    awaiting_review,
    digest_sections,
    interview_rows,
    low_credit_rows,
)
from notifications.helpers.unsubscribe import verify
from notifications.templates.emails import EMAILS

SITE = "https://testee.ai"
SECRET = "test-email-link-secret"
ALL_ON = dict.fromkeys(
    ["candidate_finished", "invite_undelivered", "ats_not_invited", "interview_ready"], True
)
COMPANIES = [
    {
        "id": "c1",
        "name": "Northwind",
        "members": [{"user_id": "ann", "editor": True}, {"user_id": "vic", "editor": False}],
    },
    {"id": "c2", "name": "Acme", "members": [{"user_id": "ann", "editor": False}]},
]


def note(company, kind, link, **data):
    return SimpleNamespace(recipient_id=company, kind=kind, link=link, data=data)


ACTIVITY = [
    note("c1", "candidate_finished", "/i1", title="Backend", count=3),
    note("c1", "candidate_finished", "/i1", title="Backend"),
    note("c1", "invite_undelivered", "/i1", title="Backend"),
    note("c2", "interview_ready", "/i2", title="Design"),
    note("c3", "candidate_finished", "/i3", title="Not ann's"),
]


def recipient(language="en"):
    return {"user_id": "ann", "email": "ann@example.com", "language": language}


def test_the_digest_groups_a_users_companies_and_adds_up_each_page():
    sections = digest_sections("ann", ALL_ON, COMPANIES, ACTIVITY, SITE)

    assert sections == [
        ("Acme", [("interview_ready", {"title": "Design", "count": 1}, f"{SITE}/i2")]),
        (
            "Northwind",
            [
                ("candidate_finished", {"title": "Backend", "count": 4}, f"{SITE}/i1"),
                ("invite_undelivered", {"title": "Backend", "count": 1}, f"{SITE}/i1"),
            ],
        ),
    ]


def test_the_digest_names_each_ats_its_candidates_were_not_invited_from():
    activity = [
        note("c2", "ats_not_invited", "/ats/greenhouse", title="Design", ats="Greenhouse"),
        note("c2", "ats_not_invited", "/ats/workable", title="Design", ats="Workable"),
    ]
    sections = digest_sections("ann", ALL_ON, COMPANIES, activity, SITE)

    assert [values["ats"] for _, values, _ in sections[0][1]] == ["Greenhouse", "Workable"]


def test_the_digest_leaves_out_kinds_turned_off_and_has_nothing_when_all_are():
    finished_off = {**ALL_ON, "candidate_finished": False}
    sections = digest_sections("ann", finished_off, COMPANIES, ACTIVITY, SITE)

    assert [row[0] for _, rows in sections for row in rows] == [
        "interview_ready",
        "invite_undelivered",
    ]
    assert digest_sections("ann", dict.fromkeys(ALL_ON, False), COMPANIES, ACTIVITY, SITE) == []
    # Not a member of any company with activity.
    assert digest_sections("zed", ALL_ON, COMPANIES, ACTIVITY, SITE) == []


def test_the_digest_is_optional_its_links_stop_the_whole_digest():
    sections = digest_sections("ann", ALL_ON, COMPANIES, ACTIVITY, SITE)
    email = digest_email(recipient(), sections, SITE, SECRET)
    token = email.headers["List-Unsubscribe"].rsplit("/", 1)[1].rstrip(">")

    assert email.subject == "Your activity digest on testee"
    assert email.headers["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    assert verify(token, SECRET) == {"type": "digest", "user_id": "ann"}
    assert "Candidates who finished: 4 · “Backend”" in email.text
    assert f"{SITE}/i1" in email.text
    assert "Unsubscribe" in email.html
    assert "Northwind" in email.html


def test_reminders_are_optional_and_open_what_they_name():
    rows = [("interview", {"title": "Backend", "company": "Acme"}, f"{SITE}/i1")]
    one = reminder_email(MemberEmail.NO_CANDIDATES, recipient(), rows, SITE, SECRET)
    two = reminder_email(MemberEmail.NO_CANDIDATES, recipient(), rows * 2, SITE, SECRET)
    credits = reminder_email(
        MemberEmail.LOW_CREDITS,
        recipient(),
        [("company", {"company": "Acme", "available": 120}, f"{SITE}/top-up")],
        SITE,
        SECRET,
    )
    token = one.headers["List-Unsubscribe"].rsplit("/", 1)[1].rstrip(">")

    assert verify(token, SECRET) == {"type": "reminders", "user_id": "ann"}
    assert f"Invite candidates: {SITE}/i1" in one.text
    assert f"Invite candidates: {SITE}/companies" in two.text
    assert f"Top up: {SITE}/top-up" in credits.text
    assert "Acme · credits available: 120" in credits.text


def test_a_failed_top_up_is_a_service_email_without_unsubscribe():
    email = top_up_failed_email(recipient(), "Acme <Co>", SITE)

    assert "Acme <Co>" in email.subject
    assert email.headers == AUTOMATED_HEADERS
    assert "unsubscribe" not in email.text.lower()
    assert "whatever your email settings" in email.text
    assert "Acme &lt;Co&gt;" in email.html
    assert f"{SITE}/top-up" in email.text


BILLING = f"{SITE}/companies/c1/billing"
NOTICE = {"price": 4500, "new_price": 5000, "currency": "USD", "date": "2026-11-21"}


@pytest.mark.parametrize(
    "build",
    [
        lambda language: top_up_paused_email(recipient(language), "Acme <Co>", BILLING),
        lambda language: price_change_email(recipient(language), "Acme <Co>", NOTICE, BILLING),
    ],
)
@pytest.mark.parametrize("language", ["en", "de", "ar"])
def test_a_paused_or_repriced_top_up_is_a_service_email_opening_the_billing_page(build, language):
    email = build(language)

    assert email.headers == AUTOMATED_HEADERS
    assert "unsubscribe" not in email.html.lower()
    assert BILLING in email.text
    assert "Acme <Co>" in email.subject
    assert "Acme &lt;Co&gt;" in email.html
    assert f'<html lang="{language}"' in email.html


@pytest.mark.parametrize(
    ("language", "notice", "old", "new", "day"),
    [
        ("en", NOTICE, "$45", "$50", "November 21, 2026"),
        ("de", {**NOTICE, "currency": "EUR"}, "45\u00a0€", "50\u00a0€", "21. November 2026"),
        # Yen have no smaller unit: 4,500 is ¥4,500.
        ("en", {**NOTICE, "currency": "JPY"}, "¥4,500", "¥5,000", "November 21, 2026"),
    ],
)
def test_a_price_notice_gives_both_prices_and_the_day_as_the_recipient_reads_them(
    language, notice, old, new, day
):
    email = price_change_email(recipient(language), "Acme", notice, BILLING)

    assert old in email.text
    assert new in email.text
    assert day in email.text


def test_member_emails_come_in_the_users_language():
    email = top_up_failed_email(recipient("de"), "Acme", SITE)

    assert email.subject == EMAILS["de"]["top_up_failed"]["subject"].format(company="Acme")
    assert '<html lang="de"' in email.html


def placeholders(text: str) -> set[str]:
    """The values a text takes; a plural block counts as its count's name."""
    text = PLURAL.sub(lambda match: "{" + match.group(1) + "}", text)

    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def flat(texts, prefix=""):
    """Every text of a language, by its path ("digest.rows.ats_not_invited")."""
    found = {}
    items = enumerate(texts) if isinstance(texts, list) else texts.items()

    for key, value in items:
        path = f"{prefix}{key}"

        if isinstance(value, str):
            found[path] = value
        else:
            found.update(flat(value, f"{path}."))

    return found


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_language_has_every_email_text_with_the_same_placeholders(language):
    english = flat(EMAILS[DEFAULT_LANGUAGE])
    texts = flat(EMAILS[language])

    assert sorted(texts) == sorted(english)

    for path, text in english.items():
        assert placeholders(texts[path]) == placeholders(text), (language, path)


def test_only_owners_and_admins_hear_about_low_credits():
    low = [{"company_id": "c1", "available": 120}, {"company_id": "gone", "available": 0}]

    assert low_credit_rows(low, COMPANIES, SITE) == {
        "ann": [("c1", ("company", {"company": "Northwind", "available": 120}, f"{SITE}/top-up"))]
    }


def test_topics_waiting_long_enough_go_to_whoever_started_them_while_they_can_act():
    now = datetime.fromisoformat("2026-10-08T09:00:00+00:00")
    two_days = "2026-10-06T08:00:00+00:00"
    generating = [
        {"id": "i1", "company_id": "c1", "generation_id": "g1"},
        {"id": "i2", "company_id": "c1", "generation_id": "g2"},
        {"id": "i3", "company_id": "c2", "generation_id": "g3"},
        {"id": "i4", "company_id": "c1", "generation_id": "g4"},
    ]
    statuses = [
        {"id": "g1", "status": "awaiting_review", "owner_uid": "ann", "updated_at": two_days},
        # Waiting less than a day, or not waiting.
        {
            "id": "g2",
            "status": "awaiting_review",
            "owner_uid": "ann",
            "updated_at": "2026-10-08T00:00:00+00:00",
        },
        {"id": "g4", "status": "running", "owner_uid": "ann", "updated_at": two_days},
        # Ann is only a viewer of c2 now.
        {"id": "g3", "status": "awaiting_review", "owner_uid": "ann", "updated_at": two_days},
    ]

    interviews, users = awaiting_review(generating, statuses, now, COMPANIES)

    # How long it has waited, in whole days: no date to format in each language.
    assert interviews == [{"id": "i1", "company_id": "c1", "generation_id": "g1", "days": 2}]
    assert users == {"i1": ["ann"]}


def test_the_review_reminder_says_how_many_days_the_topics_have_waited():
    rows = [("interview", {"company": "Acme", "days": 2}, f"{SITE}/i1")]
    english = reminder_email(MemberEmail.REVIEW_WAITING, recipient(), rows, SITE, SECRET)
    german = reminder_email(MemberEmail.REVIEW_WAITING, recipient("de"), rows, SITE, SECRET)

    assert "Acme · days waiting: 2" in english.text
    assert "Acme · Wartezeit in Tagen: 2" in german.text


def test_interview_lines_link_to_the_interview_and_skip_companies_that_are_gone():
    interviews = [
        {"id": "i1", "company_id": "c1", "title": "Backend"},
        {"id": "i9", "company_id": "gone", "title": "Old"},
    ]
    rows = interview_rows(
        interviews,
        {"i1": ["ann"], "i9": ["ann"]},
        COMPANIES,
        SITE,
        lambda interview, company: {"title": interview["title"], "company": company},
    )

    assert rows == {
        "ann": [
            (
                "i1",
                (
                    "interview",
                    {"title": "Backend", "company": "Northwind"},
                    f"{SITE}/companies/c1/interviews/i1",
                ),
            )
        ]
    }
