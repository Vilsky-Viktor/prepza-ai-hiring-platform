import re

from notifications.helpers.emails import candidate_invite_email
from notifications.helpers.markdown import markdown_html
from notifications.helpers.member_emails import digest_email

SITE = "https://prepza.ai"
INVITE = {"email": "ann@example.com", "token": "t", "title": "Backend", "company": "Acme"}


def test_an_address_and_the_pasted_link_read_left_to_right_in_arabic():
    html = candidate_invite_email({**INVITE, "language": "ar"}, SITE, "secret").html

    assert '<span dir="ltr">ann@example.com</span>' in html
    assert re.search(r'<a href="https://prepza.ai/invite/t"[^>]*dir="ltr"', html)


def test_every_table_with_text_states_the_languages_direction():
    email = digest_email(
        {"user_id": "u", "email": "ann@example.com", "language": "ar"},
        [("Acme", [("interview_ready", {"title": "Backend"}, SITE)])],
        SITE,
        "secret",
    )
    tables = re.findall(r"<table\b[^>]*>", email.html)
    # The outer one only centres the page; every other states its direction.
    stated = [table for table in tables[1:] if 'dir="rtl"' in table]

    assert len(stated) == len(tables) - 1


def test_a_list_is_indented_on_its_start_side():
    assert "padding-left:24px" in markdown_html("- one")
    assert "padding-right:24px" in markdown_html("- one", rtl=True)
