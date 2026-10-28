import re

from notifications.helpers.markdown import markdown_html, markdown_plain


def test_bold_italic_and_links_are_formatted_with_inline_styles():
    html = markdown_html("**New** and *fresh*: [see it](https://prepza.com/news?a=1&b=2)")

    assert re.search(r"<strong style=\"[^\"]+\">New</strong>", html)
    assert "<em>fresh</em>" in html
    assert re.search(
        r'<a href="https://prepza.com/news\?a=1&amp;b=2" target="_blank" style="[^"]+">see it</a>',
        html,
    )
    assert html.startswith("<p style=")


def test_lists_keep_their_items_without_paragraphs_inside():
    html = markdown_html("- one\n- two\n\n1. first\n2. second")

    assert re.findall(r"<(ul|ol) style=", html) == ["ul", "ol"]
    assert re.findall(r"<li style=\"[^\"]+\">(\w+)</li>", html) == ["one", "two", "first", "second"]
    assert "<p" not in html


def test_a_line_break_stays_a_break_and_an_empty_line_starts_a_paragraph():
    html = markdown_html("One\nTwo\n\nThree")

    assert re.search(r">One<br>\s*Two</p>", html)
    assert html.count("<p ") == 2


def test_raw_html_and_marks_the_editor_doesnt_write_stay_text():
    html = markdown_html('<script>alert(1)</script> <img src="x">\n# Heading\n`code`')

    assert "<script>" not in html and "<img" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<h1" not in html and "<code" not in html
    assert "# Heading" in html


def test_unsafe_links_are_not_links():
    html = markdown_html("[click](javascript:alert(1)) [data](data:text/html;base64,PHNjcmlwdD4=)")

    assert "<a " not in html
    assert "javascript:alert(1)" in html


def test_the_plain_text_is_the_words_alone_on_one_line():
    text = "**New**: *code* questions.\n[See them](https://prepza.com/tests)\n\n- one\n- two"

    assert markdown_plain(text) == "New: code questions. See them one two"


def test_the_plain_text_keeps_raw_html_as_text_for_the_email_to_escape():
    assert markdown_plain("A <b>bold</b> move") == "A <b>bold</b> move"
