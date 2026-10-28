import pytest
from prepza_common.config.constants import OPERATOR

from notifications.helpers.emails import candidate_invite_email
from notifications.templates.emails import EMAILS


@pytest.mark.parametrize("language", sorted(EMAILS))
def test_every_email_says_who_runs_prepza(language):
    email = candidate_invite_email(
        {
            "email": "bob@example.com",
            "token": "t",
            "title": "Backend",
            "company": "Acme",
            "language": language,
        },
        "https://prepza.example",
        "secret",
    )

    for version in (email.text, email.html):
        assert OPERATOR["name"] in version
        assert OPERATOR["address"] in version
