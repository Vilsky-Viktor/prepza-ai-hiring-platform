import base64
import hashlib
import json
import re
from html import unescape

import pytest

from notifications.constants.email import AUTOMATED_HEADERS
from notifications.constants.unsubscribe import UnsubscribeType
from notifications.helpers.emails import (
    candidate_invite_email,
    candidate_reminder_email,
    optional_email,
)
from notifications.helpers.unsubscribe import (
    address_hash,
    candidate_token,
    sign,
    user_token,
    verify,
)

SECRET = "test-email-link-secret"
SITE = "https://testee.com"
INVITE = {
    "invite_id": "6f1c2c1e-0000-4000-8000-000000000001",
    "company_id": "c-1",
    "email": "ann@example.com",
    "token": "abc",
    "title": "Backend",
    "company": "Acme & Co",
    "language": "en",
}


def tokens(text: str) -> list[str]:
    """The tokens of the unsubscribe page's links in an email, in order."""
    return re.findall(r"/unsubscribe\?token=([\w.-]+)", unescape(text))


def test_a_users_token_names_the_user_and_what_to_stop():
    token = user_token("ann", UnsubscribeType.DIGEST, SECRET)

    assert verify(token, SECRET) == {"type": "digest", "user_id": "ann"}


def test_a_candidates_tokens_name_the_address_the_company_and_for_reminders_the_invite():
    company = verify(candidate_token(INVITE, UnsubscribeType.COMPANY, SECRET), SECRET)
    reminders = verify(candidate_token(INVITE, UnsubscribeType.INVITE_REMINDERS, SECRET), SECRET)

    assert company == {
        "type": "company",
        # Links end up in request logs: the address only as its keyed hash.
        "address": address_hash("Ann@Example.com "),
        "keyed": True,
        "company_id": "c-1",
        "company": "Acme & Co",
    }
    assert "ann@example.com" not in json.dumps(company)
    # Not the plain SHA-256 anyone with the address could make.
    assert company["address"] != hashlib.sha256(b"ann@example.com").hexdigest()
    assert reminders == {**company, "type": "invite_reminders", "invite_id": INVITE["invite_id"]}


def test_a_forged_or_altered_token_is_refused():
    token = user_token("ann", UnsubscribeType.UPDATES, SECRET)
    body, signature = token.split(".")
    other = base64.urlsafe_b64encode(b'{"type":"updates","user_id":"bob"}').decode().rstrip("=")

    assert verify(token, "another-secret") is None
    assert verify(f"{other}.{signature}", SECRET) is None
    assert verify(f"{body}.{signature[:-2]}", SECRET) is None
    assert verify(body, SECRET) is None
    assert verify("", SECRET) is None


@pytest.mark.parametrize(
    "payload",
    [
        # A type that doesn't exist, or one missing what it needs.
        {"type": "newsletter", "user_id": "ann"},
        {"type": "updates"},
        {"type": "updates", "user_id": ""},
        {"type": "company", "address": "a1b2", "company": "Acme"},
        {"type": "invite_reminders", "address": "a1b2", "company_id": "c-1", "company": "Acme"},
        ["updates", "ann"],
    ],
)
def test_a_signed_token_of_the_wrong_type_or_shape_is_refused(payload):
    assert verify(sign(payload, SECRET), SECRET) is None


def test_a_signed_token_that_isnt_json_is_refused():
    body = base64.urlsafe_b64encode(b"\xff not json").decode().rstrip("=")
    token = sign({}, SECRET)

    assert verify(f"{body}.{token.split('.')[1]}", SECRET) is None


def test_the_invite_links_to_stopping_the_companys_emails():
    email = candidate_invite_email(INVITE, SITE, SECRET)
    [token] = tokens(email.html)

    assert tokens(email.text) == [token]
    assert verify(token, SECRET)["type"] == "company"
    assert ">Don't email me for Acme &amp; Co</a>" in email.html
    assert f"Don't email me for Acme & Co: {SITE}/unsubscribe?token={token}" in email.text
    # A mail client's own button stops the company's emails, at once.
    assert email.headers == {
        **AUTOMATED_HEADERS,
        "List-Unsubscribe": f"<{SITE}/api/notifications/unsubscribe/{token}>",
        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
    }


def test_the_reminder_links_to_stopping_its_reminders_or_the_companys_emails():
    email = candidate_reminder_email(INVITE, SITE, SECRET)
    reminders, company = tokens(email.html)

    assert tokens(email.text) == [reminders, company]
    assert verify(reminders, SECRET)["type"] == "invite_reminders"
    assert verify(company, SECRET)["type"] == "company"
    assert ">Don't send me reminders for this interview</a>" in email.html
    # A mail client's own button stops this invite's reminders, at once.
    assert email.headers == {
        **AUTOMATED_HEADERS,
        "List-Unsubscribe": f"<{SITE}/api/notifications/unsubscribe/{reminders}>",
        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
    }


def test_the_links_are_in_the_emails_language():
    email = candidate_reminder_email({**INVITE, "language": "de"}, SITE, SECRET)

    assert ">Keine Erinnerungen mehr zu diesem Interview</a>" in email.html
    assert ">Keine E-Mails mehr von Acme &amp; Co</a>" in email.html


def test_events_saved_before_they_named_the_company_have_no_links():
    data = {key: value for key, value in INVITE.items() if key != "company_id"}

    assert tokens(candidate_invite_email(data, SITE, SECRET).html) == []
    assert candidate_reminder_email(data, SITE, SECRET).headers == AUTOMATED_HEADERS


def test_an_optional_email_links_to_unsubscribing_and_the_email_settings():
    email = optional_email(
        "candidate", INVITE, f"{SITE}/companies", SITE, SECRET, "ann", UnsubscribeType.DIGEST
    )
    [token] = tokens(email.html)

    assert verify(token, SECRET) == {"type": "digest", "user_id": "ann"}
    assert f'href="{SITE}/settings"' in email.html
    assert ">Unsubscribe</a>" in email.html
    assert ">Change your email settings</a>" in email.html
    assert f"Change your email settings: {SITE}/settings" in email.text
    assert email.headers["List-Unsubscribe"] == f"<{SITE}/api/notifications/unsubscribe/{token}>"
    assert email.headers["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"


def test_tokens_are_compact_json_so_the_same_wish_makes_the_same_link():
    first = user_token("ann", UnsubscribeType.UPDATES, SECRET)
    body = first.split(".")[0]

    assert first == user_token("ann", UnsubscribeType.UPDATES, SECRET)
    assert json.loads(base64.urlsafe_b64decode(body + "==")) == {
        "type": "updates",
        "user_id": "ann",
    }


def test_a_link_signed_beyond_ascii_is_refused_not_an_error():
    assert verify("e30.ä", "secret") is None
