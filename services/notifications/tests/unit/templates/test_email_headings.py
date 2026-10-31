import re

from notifications.helpers.member_emails import digest_email

SITE = "https://testee.ai"


def test_an_email_has_one_h1_and_a_h2_per_section():
    email = digest_email(
        {"user_id": "u", "email": "ann@example.com", "language": "en"},
        [
            ("Acme", [("interview_ready", {"title": "Backend"}, SITE)]),
            ("Globex", [("interview_ready", {"title": "Data"}, SITE)]),
        ],
        SITE,
        "secret",
    )

    assert len(re.findall(r"<h1\b", email.html)) == 1
    assert re.findall(r"<h2\b[^>]*>([^<]*)</h2>", email.html) == ["Acme", "Globex"]
