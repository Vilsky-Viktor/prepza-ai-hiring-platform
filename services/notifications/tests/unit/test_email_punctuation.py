import pytest

from app.helpers.emails import candidate_invite_email
from app.templates.emails import EMAILS

SITE = "https://prepza.ai"
LINK = f"{SITE}/invite/t"
INVITE = {
    "email": "ann@example.com",
    "token": "t",
    "title": "Backend",
    "company": "Acme",
    "verified": False,
}


@pytest.mark.parametrize(
    ("language", "end", "colon", "between"),
    [
        ("en", ".", ": ", " "),
        ("de", ".", ": ", " "),
        ("fr", ".", " : ", " "),
        ("hi", "।", ": ", " "),
        ("ja", "。", "：", ""),
        ("zh", "。", "：", ""),
        ("th", "", ": ", " "),
    ],
)
def test_the_layouts_punctuation_is_the_languages(language, end, colon, between):
    texts = EMAILS[language]
    template = texts["candidate"]
    email = candidate_invite_email({**INVITE, "language": language}, SITE, "secret")
    footer = template.get("footer", texts["footer"]).format(**INVITE)
    note = texts["unverified"].format(**INVITE)

    assert email.text.startswith(template["heading"] + end + "\n")
    assert f"{template['button']}{colon}{LINK}" in email.text
    assert f"{footer}{between}{note}" in email.text
    assert f"{texts['paste_link']}{colon.rstrip()}<br>" in email.html
