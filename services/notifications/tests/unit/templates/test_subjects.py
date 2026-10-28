import pytest

from notifications.templates.emails import EMAILS

# Typical values: a company's and a test's names of usual length, an address, a long date.
SAMPLE = {
    "company": "Acme Corporation",
    "title": "Senior backend engineer",
    "inviter": "Alexandra",
    "candidate": "alexandra.smith@example.com",
    "date": "November 8, 2026",
    "subject": "",
}
# About 40 characters show on a phone; a subject may go a little over with long names.
LIMIT = 42


@pytest.mark.parametrize("kind", sorted(EMAILS["en"]))
def test_an_english_subject_fits_on_a_phone(kind):
    texts = EMAILS["en"][kind]

    if not isinstance(texts, dict) or "subject" not in texts:
        pytest.skip("not an email")

    assert len(texts["subject"].format(**SAMPLE)) <= LIMIT
