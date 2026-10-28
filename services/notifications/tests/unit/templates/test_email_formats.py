import pytest

from notifications.helpers.member_emails import digest_email, legal_email

SITE = "https://prepza.ai"


def recipient(language: str) -> dict:
    return {"user_id": "u", "email": "ann@example.com", "language": language}


@pytest.mark.parametrize(
    ("language", "day"),
    [("en", "November 8, 2026"), ("de", "8. November 2026"), ("fr", "8 novembre 2026")],
)
def test_a_legal_notice_names_its_day_as_the_recipients_language_writes_it(language, day):
    email = legal_email(recipient(language), "terms", "2026-11-08", SITE)

    assert day in email.subject
    assert day in email.text
    assert "2026-11-08" not in email.text


@pytest.mark.parametrize(("language", "count"), [("en", "1,234"), ("de", "1.234")])
def test_a_digests_counts_are_formatted_for_the_recipients_language(language, count):
    rows = [("candidate_finished", {"title": "Backend", "count": 1234}, SITE)]
    email = digest_email(recipient(language), [("Acme", rows)], SITE, "secret")

    assert count in email.text
    assert count in email.html
