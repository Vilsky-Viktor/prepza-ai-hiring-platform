import re
from html import escape

from babel.numbers import format_decimal
from prepza_common.config.constants import DEFAULT_LANGUAGE, OPERATOR, RTL_LANGUAGES

from app.constants.email import LTR_VALUE
from app.helpers.markdown import markdown_html
from app.models.email import Email
from app.templates.emails import EMAILS
from app.templates.layout import (
    HTML_FOOTER_LINK,
    HTML_LAYOUT,
    HTML_LOGO,
    HTML_LTR,
    HTML_NAME,
    HTML_PARAGRAPH,
    HTML_ROW,
    HTML_SECTION,
    HTML_SECTION_HEADING,
    PREHEADER_PADDING,
    TEXT_FOOTER_LINK,
    TEXT_LAYOUT,
    TEXT_ROW,
    TEXT_SECTION_HEADING,
)
from app.templates.patterns import PATTERNS

# A list under an email's text: its heading ("" for none) and its items, each the key of its
# line in the template's "rows", the values that fill it, and where it links.
Section = tuple[str, list[tuple[str, dict, str]]]


def email_language(kind: str, language: str | None) -> str:
    """The language the `kind` email is written in: English until that language has it."""
    return language if kind in EMAILS.get(language, {}) else DEFAULT_LANGUAGE


def pattern(language: str, key: str) -> str:
    """The language's way of putting pieces together (templates/patterns.py), English's while
    it has none."""
    return PATTERNS.get(language, PATTERNS[DEFAULT_LANGUAGE])[key]


def shown(value, language: str) -> str:
    """A value as the email shows it: a number formatted for the language (1,234 or 1 234)."""
    if isinstance(value, int) and not isinstance(value, bool):
        return format_decimal(value, locale=language)

    return str(value)


def render(
    kind: str,
    data: dict,
    link: str,
    links: list[tuple[str, str]] = (),
    sections: list[Section] = (),
    markdown: str = "",
) -> Email:
    """Builds the plain-text and HTML versions of the `kind` email ("candidate"), in the
    interview's language (English for older events), right to left where that language is;
    names and titles are escaped in the HTML. `sections` are lists after the text. `links` go
    under the footer: each one's text (a key of the language's texts) and address. `markdown`
    follows the template's lines (a campaign's text): as written in the plain text, formatted
    and escaped in the HTML."""
    language = email_language(kind, data.get("language"))
    texts = EMAILS[language]
    template = texts[kind]
    # An email with its own reason for being sent says so; the others share the general one.
    footer = template.get("footer", texts["footer"])

    # An invite from a company prepza hasn't verified says so, quietly, in the footer.
    if data.get("verified") is False:
        footer = pattern(language, "joined").format(first=footer, second=texts["unverified"])

    rtl = language in RTL_LANGUAGES
    labelled = pattern(language, "labelled")
    # Addresses and links keep reading left to right in a right-to-left text.
    safe = {
        key: HTML_LTR.format(text=escape(str(value)))
        if isinstance(value, str) and re.fullmatch(LTR_VALUE, value)
        else escape(str(value))
        for key, value in data.items()
    }
    emphasized = {
        **safe,
        **{
            key: HTML_NAME.format(name=safe[key])
            for key in ("company", "inviter", "sender")
            if key in safe
        },
    }

    footer_links = [(texts[key], url) for key, url in links]
    # Each list's heading and its lines, filled in.
    filled = [
        (
            heading,
            [
                (
                    template["rows"][row].format(
                        **{key: shown(value, language) for key, value in values.items()}
                    ),
                    url,
                )
                for row, values, url in rows
            ],
        )
        for heading, rows in sections
    ]

    operator = texts["operator"].format(name=OPERATOR["name"], address=OPERATOR["address"])
    text = TEXT_LAYOUT.format(
        heading=pattern(language, "sentence").format(text=template["heading"].format(**data)),
        lines="\n\n".join(
            [
                *(line.format(**data) for line in template["lines"]),
                *([markdown] if markdown else []),
            ]
        ),
        sections="".join(
            "\n"
            + (TEXT_SECTION_HEADING.format(heading=heading) if heading else "")
            + "".join(TEXT_ROW.format(text=text, url=url) for text, url in rows)
            for heading, rows in filled
        ),
        button=labelled.format(label=template["button"].format(**data), value=link),
        footer=footer.format(**data),
        operator=operator,
        links="\n"
        + "".join(
            TEXT_FOOTER_LINK.format(line=labelled.format(label=label.format(**data), value=url))
            for label, url in footer_links
        )
        if footer_links
        else "",
    )
    html = HTML_LAYOUT.format(
        subject=escape(template["subject"].format(**data)),
        preheader=template["preheader"].format(**safe),
        padding=PREHEADER_PADDING,
        heading=template["heading"].format(**safe),
        lines="\n".join(
            [
                *(
                    HTML_PARAGRAPH.format(text=line.format(**emphasized))
                    for line in template["lines"]
                ),
                *([markdown_html(markdown, rtl)] if markdown else []),
            ]
        ),
        sections="".join(
            HTML_SECTION.format(
                direction="rtl" if rtl else "ltr",
                heading=HTML_SECTION_HEADING.format(heading=escape(heading)) if heading else "",
                rows="".join(
                    HTML_ROW.format(text=escape(text), url=escape(url)) for text, url in rows
                ),
            )
            for heading, rows in filled
        ),
        button=template["button"].format(**safe),
        link=escape(link),
        footer=footer.format(**safe),
        operator=escape(operator),
        links="<br>"
        + "".join(
            HTML_FOOTER_LINK.format(text=label.format(**safe), url=escape(url))
            for label, url in footer_links
        )
        if footer_links
        else "",
        language=language,
        direction="rtl" if rtl else "ltr",
        align="right" if rtl else "left",
        paste_link=escape(labelled.format(label=texts["paste_link"], value="").rstrip()),
        logo=HTML_LOGO.format(
            url=escape(data["logo_url"]),
            alt=safe.get("company", ""),
            pad="0 16px 0 0" if rtl else "0 0 0 16px",
        )
        if data.get("logo_url")
        else "",
    )

    return Email(to=data["email"], subject=template["subject"].format(**data), html=html, text=text)
