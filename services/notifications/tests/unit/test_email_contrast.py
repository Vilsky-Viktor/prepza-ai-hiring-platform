import re

import pytest

from app.helpers.emails import candidate_invite_email
from app.helpers.member_emails import digest_email

INVITE = {
    "email": "ann@example.com",
    "token": "t",
    "title": "Backend",
    "company": "Acme",
    "company_id": "c-1",
    "invite_id": "i-1",
}
SITE = "https://prepza.ai"
# The page around the card, and the card.
PAGE, CARD = "f5f5f5", "ffffff"
# Where the card ends and the footer, on the page's background, starts.
FOOTER_START = "padding:24px 8px 0"


def luminance(colour: str) -> float:
    def channel(value: int) -> float:
        c = value / 255

        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (int(colour[i : i + 2], 16) for i in (0, 2, 4))

    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast(one: str, other: str) -> float:
    light, dark = sorted((luminance(one), luminance(other)), reverse=True)

    return (light + 0.05) / (dark + 0.05)


def text_colours(html: str) -> set[str]:
    return set(re.findall(r"(?<!background-)color:#([0-9a-fA-F]{6})", html))


@pytest.mark.parametrize(
    "email",
    [
        candidate_invite_email(INVITE, SITE, "secret"),
        digest_email(
            {"user_id": "u", "email": "ann@example.com", "language": "en"},
            [("Acme", [("interview_ready", {"title": "Backend"}, SITE)])],
            SITE,
            "secret",
        ),
    ],
)
def test_every_text_reads_at_4_5_to_1_or_more(email):
    card, footer = email.html.split(FOOTER_START, 1)
    # The wordmark's blue dot is large text (3:1 is enough), and the button's white text sits on
    # its blue: both are checked apart.
    body = card[card.index("<h1") :]

    assert {
        c: round(contrast(c, PAGE), 2) for c in text_colours(footer) if contrast(c, PAGE) < 4.5
    } == {}
    assert {
        c: round(contrast(c, CARD), 2)
        for c in text_colours(body) - {"ffffff"}
        if contrast(c, CARD) < 4.5
    } == {}
    assert contrast("ffffff", "0071e0") >= 4.5
